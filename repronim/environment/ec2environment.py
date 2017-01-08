# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the repronim package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Environment sub-class to provide management of an AWS EC2 instance."""

import boto3
from sys import version_info, exit
from os import makedirs, chmod, getcwd
from os.path import expanduser, dirname, exists, isfile

from repronim.environment.base import Environment
from repronim.support.sshconnector2 import SSHConnector2


class Ec2Environment(Environment):

    def __init__(self, config={}):
        """
        Class constructor

        Parameters
        ----------
        config : dictionary
            Configuration parameters for the environment.
        """
        if not 'base_image_id' in config:
            config['base_image_id'] = 'ami-c8580bdf' # Ubuntu 14.04 LTS
        if not 'instance_type' in config:
            config['instance_type'] = 't2.micro'
        if not 'security_group' in config:
            config['security_group'] = 'default'

        super(Ec2Environment, self).__init__(config)

        self._ec2_resource = None
        self._ec2_instance = None

        # Initialize the connection to the AWS resource.
        aws_client = self.get_resource_client()
        self._ec2_resource = boto3.resource(
            'ec2',
            aws_access_key_id=aws_client['aws_access_key_id'],
            aws_secret_access_key=aws_client['aws_secret_access_key'],
            region_name=self['region_name']
        )

    def create(self, name, image_id):
        """
        Create an EC2 instance.

        Parameters
        ----------
        name : string
            Name identifier of the environment to be created.
        image_id : string
            Identifier of the image to use when creating the environment.
        """
        if name:
            self['name'] = name
        if image_id:
            self['base_image_id'] = image_id
        if not 'key_name' in self:
            self.create_key_pair()

        instances = self._ec2_resource.create_instances(
            ImageId=self['base_image_id'],
            InstanceType=self['instance_type'],
            KeyName=self['key_name'],
            MinCount=1,
            MaxCount=1,
            SecurityGroups=[self['security_group']],
        )

        # Give the instance a tag name.
        self._ec2_resource.create_tags(
            Resources=[instances[0].id],
            Tags=[{'Key': 'Name', 'Value': self['name']}]
        )

        # Save the EC2 Instance object.
        self._ec2_instance = self._ec2_resource.Instance(instances[0].id)

        self._lgr.info("Waiting for EC2 instance %s to start running...", self._ec2_instance.id)
        self._ec2_instance.wait_until_running(
            Filters=[
                {
                    'Name': 'instance-id',
                    'Values': [self._ec2_instance.id]
                },
            ]
        )
        self._lgr.info("EC2 instance %s to start running!", self._ec2_instance.id)

        self._lgr.info("Waiting for EC2 instance %s to complete initialization...", self._ec2_instance.id)
        waiter = self._ec2_instance.meta.client.get_waiter('instance_status_ok')
        waiter.wait(InstanceIds=[self._ec2_instance.id])
        self._lgr.info("EC2 instance %s initialized!")

    def connect(self, name):
        """
        Open a connection to the environment.

        Parameters
        ----------
        name : string
            Name identifier of the environment to connect to.
        """
        instances = self._ec2_resource.instances.filter(
            Filters=[{
                'Name': 'tag:Name',
                'Values': [name]
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }]
        )
        instances = list(instances)
        if len(instances) == 1:
            self._ec2_instance = instances[0]
        else:
            raise Exception("AWS error - No EC2 instance named {}".format(name))

    def execute_command(self, ssh, command, env=None):
        """
        Execute the given command in the environment.

        Parameters
        ----------
        ssh : SSHConnector2 instance
            SSH connection object
        command : list
            Shell command string or list of command tokens to send to the
            environment to execute.
        env : dict
            Additional (or replacement) environment variables which are applied
            only to the current call
        """
        command_env = self.get_updated_env(env)

        # if command_env:
            # TODO: might not work - not tested it
            # command = ['export %s=%s;' % k for k in command_env.items()] + command

        # If a command fails, a CommandError exception will be thrown.
        for i, line in enumerate(ssh(" ".join(command))):
            self._lgr.debug("exec#%i: %s", i, line.rstrip())

    def execute_command_buffer(self):
        """
        Send all the commands in the command buffer to the environment for
        execution.
        """
        host = self._ec2_instance.public_ip_address
        key_filename = self['key_filename']

        with SSHConnector2(host, key_filename=key_filename) as ssh:
            for command in self._command_buffer:
                self._lgr.info("Running command '%s'", command['command'])
                self.execute_command(ssh, command['command'], command['env'])

    def create_key_pair(self):
        """
        Walk the user through creating an SSH key pair that is saved to
        the AWS platform.
        """

        def get_user_input(prompt):
            py3 = version_info[0] > 2
            if py3:
                response = input(prompt)
            else:
                response = raw_input(prompt)
            return response.strip()

        # Prompt for a name of the key-pair on AWS.
        prompt = """
You did not specify an EC2 SSH key-pair name to use when creating your EC2 environment.
Please enter a unique name to create a new key-pair or press [enter] to exit.> """
        key_name = get_user_input(prompt)

        # The user wants to exit.
        if not key_name:
            exit(0)

        # Check to see if key_name already exists.
        for i in range(3):
            key_pairs = self._ec2_resource.key_pairs.filter(KeyNames=[key_name])
            try:
                len(list(key_pairs))
            except:
                # Catch the exception raised when there is no matching key name at AWS.
                break
            if i == 2:
                print('That key name exists already, exiting.')
                exit(1)
            else:
                prompt = 'That key name exists already, try again. > '
                key_name = get_user_input(prompt)

        # Prompt for a path to store the SSH private key.
        default_path = '{}/.ssh/{}.pem'.format(expanduser("~"), key_name)
        for i in range(3):
            prompt = 'Please enter the path to save the private key. [{}]> '.format(default_path)
            key_filename = get_user_input(prompt)

            if not key_filename:
                key_filename = default_path
            # Put .pem at end of private key file if not there already.
            elif not key_filename.endswith('.pem'):
                key_filename += '.pem'

            if isfile(key_filename):
                if i == 2:
                    print('File exists, exiting.')
                    exit(1)
                else:
                    # TODO: Ask user if they want to overwrite the existing file.
                    print('File exists, try again.')
            else:
                break

        # Make sure the directory for the private key file exists.
        basedir = dirname(key_filename)
        if not basedir or not basedir.startswith('/'):
            basedir = getcwd()
            key_filename = basedir + '/' + key_filename
        if not exists(basedir):
            makedirs(basedir)

        # Generate the key-pair and save to the private key file.
        with open(key_filename, 'w') as key_file:
            key_pair = self._ec2_resource.create_key_pair(
                DryRun=False,
                KeyName=key_name
            )
            key_file.write(key_pair.key_material)
        chmod(key_filename, 0o400)
        self._lgr.info("Created private key file %s.", key_filename)

        # Save the new info to the resource.
        self['key_name'] = key_name
        self['key_filename'] = key_filename
        # TODO: Write new config info to the repronim.cfg file.
