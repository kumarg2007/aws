import boto3
import botocore
import os



Imageselection = {}
Inst = 0


ec2 = boto3.resource('ec2')
client = boto3.client('ec2')

#j=client.describe_security_groups()
#i = j['SecurityGroups']

#print (j['SecurityGroups'][0]['GroupName'])
        
def display_imagename():
    """
     This function shows the image to deploy and the selection of the Imageid as the returnvalue
     1) The below response dict will collect the details of imageid listed in the **kwargs
     2) Passing to the list
     3) Intiating a Counter
     4) Subscripting the list                                   
     5) Creating a dictionary with image name
     6) Incrementing the counter till the images are listed
     7) Looping through newly created dict items
     8) Print formatted output
     9) Title to input the image number
     10) While loop starts
     11) try loop
     12  Asking the customer to enter the number
     13) Checking the number against the total items
     14) Passing the image to variable
     15) looping the mage list
     16) Comparing the image name
     17) if there is match returnn the imageid and exit
     18) if the number out of range ask to re-enter
     19) Displaying wrong message
     20) if its not number raised error
     21 Message dispaly continue
    """
    response = client.describe_images(ImageIds=['ami-a2c111c1','ami-3f03c55c','ami-e113c082'],Filters=[{'Name':'root-device-type','Values':['ebs'],'Name': 'architecture','Values':['x86_64'],'Name':'platform','Values':['windows','Redhat'],'Name':'virtualization-type','Values':['hvm']}])
    Imagelist = response['Images']                                   
    x = 1                                                           
    for desc in Imagelist:                                          
        Imageselection[x] = desc['Name']                            
        x+=1                                                       
    for key,values in Imageselection.items():                      
        print('{0}==>{1}'.format(key,values))
    print("\n")                      
    while True:                                                     
        try:    
           print('\n')                                                    
           num = int(input("Enter a Image Number: "))                       
           if (num <= len(Imageselection.keys())):                    
               selectionimage = Imageselection[num]                   
               for desc in Imagelist:                               
                   if (selectionimage == desc['Name']):               
                       return (desc['ImageId'])                     
           else:                                                    
               print("\nSorry Wrong image:")                        
        except ValueError:
             print("\nSorry Wrong Selection:")
                
             
          
def createsecuritygroup():
    """
    Creating security group and adding a rule on port 80 for ingress traffic.
    1) Asking the name for secuity group
    2) Asking the Description for group
    3) Asking for the portnumber
    4) converting the portnumber to list
    5) Creating the security group on default VPC
    6) Passing the portnum as paramter to authorize_ingress
    7) if group name already exist then exception error InvalidGroup.Duplicate
    8) if Inst=1 means webserver had selected and return secgrp for default VPC
    9) if Inst not equal 1 means DB server in this context return Group-id for internal subnet
    """
    while True:
        secgrp = input("Enter the security group name:  ")
        grpdesc = input("Enter the Description: ")
        portnumber = input("Enter the port number Multiple port number with Space in between:")
        portlist = list(map(int,portnumber.split()))
        
        try:
            response = ec2.create_security_group(GroupName=secgrp,Description=grpdesc,VpcId='vpc-148f1971')                 
            if response:
                for portnum in portlist: 
                    response.authorize_ingress(IpProtocol='tcp',FromPort=portnum,ToPort=portnum,CidrIp='0.0.0.0/0')
                    
            if Inst==1:
                return secgrp
            else:
                Getgroupid = client.describe_security_groups()
                getgroupidlist = Getgroupid['SecurityGroups']
                for secid in getgroupidlist:
                    if secid['GroupName'] == secgrp:
                        return (secid['GroupId'])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidGroup.Duplicate':
                print("Group name already exists")
                continue

#y=createsecuritygroup()
#print(y)            

def create_key():
    """
       Creating the keypair for login the system
       1) Inputting a file Name
       2) Path to save the file
       3) Creating keypair in AWS
       4) Join the path with file name
       5) open the file if the file not create  new one  
       6) Iterting the dict
       7) Matching the key against AWS response dict
       8) Writing the value
       9) Close the file  
    """
    while True:
        try:
            Pemfile = input("\nPlease specify the name of the keyfile for passwordless login: ")
            Save_path = "E:\AWS\Key"
            keypair = client.create_key_pair(KeyName=Pemfile)
            completeName = os.path.join(Save_path,Pemfile + ".pem")
            fo = open(completeName,"w")
            for keys,values in keypair.items():
                if keys == 'KeyMaterial':
                    fo.write(values)
                    fo.close()
            return Pemfile
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
                print("Key already exist")
                continue

def userdata():

    """ The shell script will run once at the time of creating the Instance"""
    if (Inst==1):
        myscript = """#!/bin/bash
        yum update -y
        yum install -y httpd24 php56 mysql55-server php56-mysqlnd
        service httpd start
        chkconfig httpd on
        groupadd www
        usermod -a -G www ec2-user
        chown -R root:www /var/www
        chmod 2775 /var/www
        find /var/www -type d -exec chmod 2775 {} +
        find /var/www -type f -exec chmod 0664 {} +
        echo "<?php phpinfo(); ?>" > /var/www/html/phpinfo.php"""  

        return myscript
    elif (Inst==2):
       myscript = """#!/bin/bash
       yum update -y
       yum install -y httpd24 php56 mysql55-server php56-mysqlnd
       yum-config-manager --enable epel
       yum install -y phpMyAdmin
       sudo sed -i -e 's/127.0.0.1/118.201.61.58/g' /etc/httpd/conf.d/phpMyAdmin.conf
       sudo sed -i '85s/FALSE/TRUE/' /etc/phpMyAdmin/config.inc.php	
       service httpd start
       chkconfig httpd on
       sudo service mysqld start
       chkconfig mysqld on
       groupadd www
       usermod -a -G www ec2-user
       chown -R root:www /var/www
       chmod 2775 /var/www
       find /var/www -type d -exec chmod 2775 {} +
       find /var/www -type f -exec chmod 0664 {} +
       """  

       return myscript



def launch_instance():
    """
    1) The variable Inst to store the selection value of Web Server or DB Server
    2) The Server Dictionary to hold the Server Name
    3) Sorted the Dictionary
    4) Print statement for asking the Instance
    5) Print the key & values for Display
    6) Ask for the Input
    7) if Selection is 1 or WebServer then create instace without subnet-id
    8) if the Selction is 2 or Db Server then the create instance will run with subnet-id and Group-id
    9) If it's 0 then Break
    10) Any other number will display wrong entry
    11) Instance creation
    12) Print waiting
    13) Succesful creation of Instance will display the Instance-Id Instance State, Instance Public IP address,Instance Public DNS Name.
    14) Print statement for asking for creating new instance
    15) Input for YES or NO
    16 If Yes continue else break from the fuction. 
    """
    global Inst
    Server ={'1':"WEBSERVER",'2':"DBSERVER",'0':"Exit"}
    sorted(Server)
    print("Please select the Server Instance:\n" )
    for key,values in Server.items():
        print("\t {0},{1}".format(key,values))

    while True:
        try:
            Inst = int(input("\nEnter the Instancetype==> "))
            if (Inst==1):
                instances = ec2.create_instances(ImageId=display_imagename(),InstanceType='t2.micro',MinCount=1,MaxCount=1,KeyName=create_key(),UserData=userdata(),SecurityGroups=[createsecuritygroup()])
            elif (Inst==2):
                instances = ec2.create_instances(ImageId=display_imagename(),InstanceType='t2.micro',MinCount=1,MaxCount=1,KeyName=create_key(),UserData=userdata(),SecurityGroupIds=[createsecuritygroup()],SubnetId='subnet-5b27e83f')
            elif (Inst==0):
                break                
            else:
                print("WRONG ENTRY")
            for instance in instances:
                print("Waiting .........................")
                instance.wait_until_running()
                instance.reload()
                print((instance.id,instance.state,instance.public_ip_address,instance.public_dns_name))

            print("\nDo you want create one more Instance: ")
            ans=input("Enter Y or N:")
            if (ans=='Y'):
                continue
            elif (ans=='N'):
                break
            else:
                print ("Wrong Entry")               
        except ValueError:
            print("\nSorry Wrong Selection:")
            
    


launch_instance()