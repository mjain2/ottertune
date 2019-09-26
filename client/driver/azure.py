import json
import logging
import os
import time
import warnings
from subprocess import call, check_output, PIPE
from collections import OrderedDict

from cloudproviderbase import CloudProviderBase, VirtualMachine, Database, VirtualAKS, CloudProviders

# example use:
# import Azure
# my_azure_provider = Azure(region, subscription_id, resource_group_name)

class Azure(CloudProviderBase):
    def __init__(self, region, subscription_id, resource_group):
        self.resource_group = resource_group
        self.subscription = subscription_id

        self.logged_in = None

        super().__init__(region)

    def login(self):
        # login
        if call("az account show", shell=True, stdout=PIPE) != 0:
            call("az login", shell=True)
            if call("az account show", shell=True) != 0:
                return False

        # setup subscription
        if call(f"az account set --subscription {self.subscription}", shell=True, stdout=PIPE) != 0:
            return False

        # setup resource group
        if call(f"az group show --name {self.resource_group}", shell=True, stdout=PIPE) != 0:
            print(f"Creating new resource group name: {self.resource_group}")
            if call(f"az group exists --name {self.resource_group}", shell=True, stdout=PIPE) == False:
                if call(f"az group create --name {self.resource_group} --location {self.region}", shell=True, stdout=PIPE) != 0:
                    return False

        self.logged_in = True
        logging.log(logging.INFO,f"logged in: {self.logged_in}")
        return True

    # restart the server through azure CLI
    def restart_server(self, database_type, server_name):
        if not self.logged_in:
            warnings.warn("You are not logged into Azure")
            return None

        if (database_type != "mysql" and database_type != "postgres"):
            warnings.warn("Not a valid database to be restarted.")
            return None

        command_restart_server = (
            f"az {database_type} server restart "
            f"--name {server_name} "
            f"--resource-group {self.resource_group} "
            f"--subscription {self.subscription}"
        )

        if call(command_restart_server, shell=True, stdout=PIPE) != 0:
            return None
        
        return True

    # example to path_to_cnf: next_config (within driver folder)
    def apply_config_batch(self, database_type, server_name, path_to_cnf):
        if not self.logged_in:
            warnings.warn("You are not logged into Azure")
            return None
        
        if database_type != "mysql":
            warnings.warn("Not a valid database to apply configs.")
            return None
        
        # similar to ConfParser.py in Ottertune - but open the next_config to apply those values
        conf_file = open(path_to_cnf)
        config = json.load(conf_file, encoding="UTF-8", object_pairs_hook=OrderedDict)
        recommendation = config['recommendation']

        for (knob_name, knob_value) in list(recommendation.items()):
            completed = self.apply_config_internal(database_type, server_name, knob_name, knob_value)
            if completed is None:
                warnings.warn(f"Did not apply config for {knob_name}")

        return True
        

    def apply_config_internal(self, database_type, server_name, config_name, value):
        command_apply_config = (
             f"az {database_type} server configuration set "
            f"--name {config_name} "
            f"--resource-group {self.resource_group} "
            f"--server {server_name} "
            f"--value {value}"
        )

        if call(command_apply_config,shell=True, stdout=PIPE) != 0:
            return None
        
        logging.info(f"Applied configuration {config_name} with value {value} to the server {server_name}.")
        return True

    def create_database(self, database_type, server_name, database_name):
        command_create_database = (
             f"az {database_type} db create "
            f"--name {database_name} "
            f"--resource-group {self.resource_group} "
            f"--subscription {self.subscription} "
            f"--server-name {server_name}"
        )

        if call(command_create_database,shell=True, stdout=PIPE) != 0:
            return None
        
        return True

    def drop_database(self, database_type, server_name, database_name):
        command_drop_database = (
             f"az {database_type} db delete "
            f"--name {database_name} "
            f"--resource-group {self.resource_group} "
            f"--subscription {self.subscription} "
            f"--server-name {server_name}"
        )

        if call(command_drop_database,shell=True, stdout=PIPE) != 0:
            return None
        
        return True

    def provision_vm(self, public_key, private_key, username="vmuser", size="Standard_B2s", image="UbuntuLTS"):  # pylint: disable=arguments-differ
        if not self.logged_in:
            warnings.warn("You are not logged into Azure")
            return None

        name = self.vm_name + self.generate_uid()
        command_create_vm = (
            f"az vm create "
            f"--resource-group  {self.resource_group} "
            f"--name            {name} "
            f"--image           {image} "
            f"--admin-username  {username} "
            f"--ssh-key-value   {public_key} "
            f"--subscription    {self.subscription} "
            f"--size            {size}"
        )
        if call(command_create_vm, shell=True, stdout=PIPE) != 0:
            return None

        # return the public IP address
        raw_output = check_output(f"az network public-ip show --name {name}PublicIP --resource-group {self.resource_group} --query ipAddress", shell=True)
        clean_ip = json.loads(raw_output.decode('utf-8'))

        return VirtualMachine(name, clean_ip, private_key, username, cloud=CloudProviders.Azure)

    def provision_aks(self):
        if not self.logged_in:
            warnings.warn("You are not logged into Azure")
            return False

        cluster_name = self.vm_name + self.generate_uid()
        pod_name = "pgbench-pod"
        node_count = "1"
        command_create_aks = (
            f"az aks create "
            f"--resource-group  {self.resource_group} "
            f"--name            {cluster_name} "
            f"--node-count      {node_count}"
        )
        logging.info(f"Azure Kubernetes-- cluster name: {cluster_name}, command: {command_create_aks}")
        if call(command_create_aks, shell=True) != 0:
            return False

        command_get_credentials = (
            f"az aks get-credentials "
            f"--resource-group  {self.resource_group} "
            f"--name            {cluster_name} "
            f"--overwrite-existing"
        )
        logging.info(f"Azure Kubernetes-- cluster name: {cluster_name}, command:{command_get_credentials}")
        if call(command_get_credentials, shell=True) != 0:
            return False

        conf_file = open("./provisioner.conf")
        pg_password = json.load(conf_file)["db_password"]
        conf_file.close()
        aks_template_file_path = "./src/PerformanceTesting/Provisioner/CloudProviders/Resources/aks_pod_example.yaml"
        example_file = open(aks_template_file_path)
        aks_file_content = example_file.read()
        example_file.close()
        aks_yaml_file_path = "./src/PerformanceTesting/Provisioner/CloudProviders/Resources/aks_pod.yaml"
        aks_file = open(aks_yaml_file_path, "w")
        aks_file_content = aks_file_content.replace("$PODNAME$", pod_name)
        aks_file_content = aks_file_content.replace("$PGPASSWORD$", pg_password)
        aks_file.write(aks_file_content)
        aks_file.close()
        command_create_pod = f"kubectl create -f {aks_yaml_file_path}"
        logging.info(f"Azure Kubernetes-- cluster name: {cluster_name}, command: {command_create_pod}")

        if call(command_create_pod, shell=True) != 0:
            return False

        time.sleep(30)
        os.remove(aks_yaml_file_path)

        def install(command):
            logging.info(f"Azure Kubernetes-- cluster name: {cluster_name}, command: {command}")
            call(f"kubectl exec {pod_name} -- {command}", shell=True)

        install("apt-get update")
        install("apt-get install -y postgresql-contrib")
        install("apt-get --assume-yes install python3.5")
        install("apt-get --assume-yes install python-psycopg2")

        return VirtualAKS(self.resource_group, cluster_name, pod_name)

    def provision_pg(self, password, username="pguser", sku="GP_Gen5_2", storage=100, version="10"):  # pylint: disable=arguments-differ
        return self._provision_db_internal_("postgres", password, username=username, sku=sku, storage=storage, version=version)

    def provision_mysql(self, password, username="mysqluser", sku="GP_Gen5_2", storage=100, version="5.7"):  # pylint: disable=arguments-differ
        return self._provision_db_internal_("mysql", password, username=username, sku=sku, storage=storage, version=version)

    def _provision_db_internal_(self, database_type, password, username, sku, storage, version):
        if not self.logged_in:
            warnings.warn("You are not logged into Azure")
            return None

        name = database_type + self.generate_uid()
        command_create_db = (
            f"az {database_type} server create "
            f"--resource-group  {self.resource_group} "
            f"--name            {name} "
            f"--location        {self.region} "
            f"--admin-user      {username} "
            f"--admin-password  {password} "
            f"--sku-name        {sku} "
            f"--version         {version} "
            f"--storage-size    {storage * 1024} "
        )
        if call(command_create_db, shell=True, stdout=PIPE) != 0:
            return False

        command_open_firewall = (
            f"az {database_type} server firewall-rule create "
            f"--resource-group   {self.resource_group} "
            f"--server           {name} "
            f"--name             ClientIPRule "
            f"--start-ip-address 0.0.0.0 "
            f"--end-ip-address   255.255.255.255 "
        )
        if (call(command_open_firewall, shell=True, stdout=PIPE)) != 0:
            warnings.warn(f"Firewall rule creation failed")

        hostname = check_output(f"az {database_type} server show --name {name} --resource-group {self.resource_group} --query fullyQualifiedDomainName",
                                shell=True)
        hostname = json.loads(hostname.decode("utf-8"))

        return Database(hostname, f"{username}@{name}", password, engine=database_type, cloud=CloudProviders.AWS)

    def clean_up(self):
        if call(f"az group show --name {self.resource_group}", shell=True, stdout=PIPE) == 0:
            if call(f"az group delete --resource-group {self.resource_group} --yes", shell=True) != 0:
                if call(f"az group show --name {self.resource_group}", shell=True, stdout=PIPE) == 0:
                    warnings.warn(f"Resource Group {self.resource_group} failed to delete itself ")
                    return False

        print(f"Resource Group {self.resource_group} was removed ")
        return True
