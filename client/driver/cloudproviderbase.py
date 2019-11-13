import enum
import random
from abc import ABC, abstractmethod
from subprocess import call


# CloudProviderBase provides class variables, abstract methods, and common methods
# that extend to its children classes

class CloudProviders(enum.Enum):
    Azure = "azure"
    AWS = "aws"
    GCP = "gcp"


class CloudProviderBase(ABC):
    def __init__(self, region):
        self.region = region
        self.vm_name = "client"
        super().__init__()

    @abstractmethod
    def login(self):
        raise NotImplementedError

    @abstractmethod
    def provision_vm(self):
        raise NotImplementedError

    @abstractmethod
    def provision_aks(self):
        raise NotImplementedError

    @abstractmethod
    def provision_pg(self, password):
        raise NotImplementedError

    @abstractmethod
    def provision_mysql(self, password):
        raise NotImplementedError

    @abstractmethod
    def clean_up(self):
        raise NotImplementedError

    @classmethod
    def generate_uid(cls):
        # generate a random 5 digit UID
        return str(random.randint(10000, 100000))

    def __str__(self):
        return str(vars(self))


class VirtualMachine:
    def __init__(self, name, ip, private_key_path, username, cloud=None, size=None):
        self.name = name
        self.ip = ip
        self.private_key_path = private_key_path
        self.username = username
        self.cloud = cloud
        self.size = size

    def sendCommand(self, command):
        cmd = f'ssh -o "StrictHostKeyChecking no" {self.username}@{self.ip} -i {self.private_key_path} "{command}"'
        call(cmd)

    def copyFile(self, file_path):
        call(f'scp -i {self.private_key_path} {file_path} {self.username}@{self.ip}:~/')

    def copyDir(self, src_dir, dst_dir):
        call(f'scp -r -i{self.private_key_path} {src_dir} {self.username}@{self.ip}:{dst_dir}')

    def __str__(self):
        return str(vars(self))


class Database:
    def __init__(self, hostname, username, password, engine=None, size=None, version=None, storage=None, cloud=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.engine = engine
        self.size = size
        self.version = version
        self.storage = storage
        self.cloud = cloud

    def __str__(self):
        return str(vars(self))


class VirtualAKS:
    def __init__(self, resource_group, cluster_name, pod_name):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.pod_name = pod_name

    def execute_command(self, command):
        print(command)
        call(f"kubectl exec {self.pod_name} -- /bin/bash -c {command}", shell=True)

    def copy_file(self, file_path, expected_file_path):
        call(f"kubectl cp {file_path} {self.pod_name}:/{expected_file_path}")

    def aws_clean_up(self):
        call(f"aws cloudformation delete-stack --stack-name EKS-{self.cluster_name}-DefaultNodeGroup", shell=True)
        call(f"aws cloudformation delete-stack --stack-name EKS-{self.cluster_name}-ControlPlane", shell=True)
        call(f"aws cloudformation delete-stack --stack-name EKS-{self.cluster_name}-VPC", shell=True)
        call(f"aws cloudformation delete-stack --stack-name EKS-{self.cluster_name}-ServiceRole", shell=True)
        call(f"aws ec2 delete-key-pair --key-name eksctl-{self.cluster_name}-7a:aa:b0:fb:73:0a:c3:a2:91:c9:ac:38:19:73:47:b8", shell=True)

    def __str__(self):
        return str(vars(self))
