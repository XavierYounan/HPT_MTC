#!/bin/env python
#
# show_job. shows a users's job list nad summary
# substantially modified by Simon Michnowicz 22 Feb 19
#
import os
import sys
import subprocess
import time
import datetime
import re
import getpass
from prettytable import PrettyTable

################################################
# in case we want coloured output
#from termcolor import colored, cprint
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKRED = '\033[31m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


#debugging is enabled by this flag
#debug=True
debug=False

class show_job():

    SCONTROL="scontrol"
    SQUEUE="squeue"
    SINFO="sinfo"
    SITE=""

    PartitionList=[]
    # UPDATE THESE PARITION NAMES AS THEY CHANGE
    M3_PARTITIONS=["comp", "desktop","com" ,"short","m3i","m3m","m3g","m3h","m3f","m3d","m3a"]
    MONARCH_PARTITIONS=["comp","gpu","short"]

    ################################################
    @classmethod
    def set_site(self):
        '''
        sets the site variable based on hostname
        '''
        #global SITE
        #global PartitionList
        command="hostname"
        if debug:
            print("set_site: Before command {}".format(command))
        system_command=subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        hostname=system_command.communicate()[0].decode('utf-8').strip('\n')
        if ( "m3" in hostname):
            self.SITE="M3"
            self.PartitionList=self.M3_PARTITIONS
            #print(PartitionList)
            return
        if ( "monarch" in hostname):
            self.SITE="MonARCH"
            self.PartitionList=self.MONARCH_PARTITIONS
            #print(PartitionList)
            return
        print("ERROR: we can not determine the cluster we are on. Please contact help")
        self.SITE="Unknown"

    ################################################
    @classmethod
    def get_path(self,exeName):
        '''
        gets true path of exeName by `which`
        if no path found we should exit script
        '''
        command="which {}".format(exeName)
        try:
            result = subprocess.check_output(command.split())
            return result.decode('utf-8').rstrip()
        except subprocess.CalledProcessError as error:
            print("get_path  command  \"{}\" failed. error. error code".format(command, error.returncode, error.output))
            sys.exit(1)


    ################################################
    @classmethod
    def find_slurm_paths(self):
        '''
        this script may be called from an environment that does not have SLURM in the PATH
        It attempts to find slurm binaries from default path and if not, then searches for it in a predefined
        list SEARCH_PATHS_FOR_SLURM
        '''
        #global SCONTROL
        #global SQUEUE
        #global SINFO
        self.SCONTROL=self.get_path(self.SCONTROL)
        self.SQUEUE=self.get_path(self.SQUEUE)
        self.SINFO=self.get_path(self.SINFO)
        
        #sanity checks
        if (not os.path.isfile(self.SCONTROL)):
            print("We can not find exe {} ".format(self.SCONTROL))
            sys.exit(1)
        if (not os.path.isfile(self.SINFO)):
            print("We can not find exe {} ".format(self.SINFO))
            sys.exit(1)
        if (not os.path.isfile(self.SQUEUE)):
            print("We can not find exe {} ".format(self.SQUEUE))
            sys.exit(1)
    

    ################################################
    @classmethod
    def Check_Single_Job (self,Job_ID):
        try:
            if debug:
                print("Check_Single_Job: Job_id={}".format(Job_ID))
            command=self.SQUEUE+" --format=%s -h | grep %s" % ("%A",Job_ID)
            squeue_command=subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            squeue_info=squeue_command.communicate()[0].decode('utf-8').rstrip('\n')
            if not squeue_info:
                return

            command=self.SCONTROL+" show job %s" % Job_ID
            job_command=subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            job_info=job_command.communicate()[0].decode('utf-8').rstrip('\n')
            if debug: print("Check_Single_Job, job_info={}".format(job_info))
            userName=job_info.split("UserId=")[1].split("(")[0]
            fullUserName=self.getFullUserName(userName)
            command="username2email {}".format(userName)
            system_command=subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            EMAIL_ADDR=system_command.communicate()[0].decode('utf-8').rstrip('\n').strip()

            Job_Name=job_info.split("JobName=")[1].split("\n")[0]
            Project=job_info.split("Account=")[1].split()[0]
            QoS=job_info.split("QOS=")[1].split("\n")[0]
            Job_State=job_info.split("JobState=")[1].split()[0]
            Job_Reason=job_info.split("Reason=")[1].split()[0]
            Job_Dependency=job_info.split("Dependency=")[1].split("\n")[0]
            Job_Running_time=job_info.split("RunTime=")[1].split()[0]
            Job_Total_Time=job_info.split("TimeLimit=")[1].split()[0]
            Partition=job_info.split("Partition=")[1].split()[0]
            Sub_Host=job_info.split("AllocNode:Sid=")[1].split(":")[0]
            Sub_Time=job_info.split("SubmitTime=")[1].split()[0]
            Job_NumNodes=job_info.split("NumNodes=")[1].split()[0]
            Job_NumCPUs=job_info.split("NumCPUs=")[1].split()[0]
            Job_CPUsPerTask=job_info.split("CPUs/Task=")[1].split()[0]
            Job_StartTime=job_info.split("StartTime=")[1].split()[0]
            Job_Outfile="N/A"
            Job_Errfile="N/A"

            if "MinCPUsNode" in job_info:
                Job_MinCPUsNode=job_info.split("MinCPUsNode=")[1].split()[0]
            if "MinMemoryCPU" in job_info:
                Job_MemoryPerCpu=job_info.split("MinMemoryCPU=")[1].split()[0]
            if "MinMemoryNode" in job_info:
                Job_MinMemoryNode=job_info.split("MinMemoryNode=")[1].split()[0]
    
            if "Job_Gres" in job_info:
               Job_Gres=job_info.split("Gres=")[1].split()[0]
            else:
                Job_Gres="N/A"
            Job_Constraint=job_info.split("Features=")[1].split()[0]
            Job_Command=job_info.split("Command=")[1].split()[0]
            Job_WorkDir=job_info.split("WorkDir=")[1].split()[0]
            if "StdOut" in job_info:
                Job_Outfile=job_info.split("StdOut=")[1].split()[0]
            if "StdErr" in job_info:
                Job_Errfile=job_info.split("StdErr=")[1].split()[0]


            x = PrettyTable()
            title=bcolors.OKBLUE+bcolors.BOLD+"JOB SUMMARY: {}".format(Job_ID)+bcolors.ENDC +"                                                    "
            print(title)
            col1="Summary"
            col2="Value"
            divider="----------------------------------"
            x.field_names=[col1,col2]
            x.align[col1]="l"
            x.align[col2]="l"
    
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"JobID"+bcolors.ENDC, Job_ID])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Username"+bcolors.ENDC, userName])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Name"+bcolors.ENDC, fullUserName])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Email"+bcolors.ENDC, EMAIL_ADDR])
            x.add_row([divider,divider])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Job Name"+bcolors.ENDC, Job_Name])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Project"+bcolors.ENDC, Project])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Partition"+bcolors.ENDC, Partition])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"QOS"+bcolors.ENDC,QoS])
    
            if Job_State == "RUNNING":
                x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Job Start Time"+bcolors.ENDC,bcolors.OKGREEN+Job_StartTime+bcolors.ENDC])
                x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Job State"+bcolors.ENDC,bcolors.OKGREEN+Job_State+bcolors.ENDC])
            else:
                x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Estimated Job Start Time"+bcolors.ENDC,bcolors.OKRED+Job_StartTime+bcolors.ENDC])
                x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Job State"+bcolors.ENDC,bcolors.OKRED+Job_State+bcolors.ENDC])
                x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Why Can't run"+bcolors.ENDC,bcolors.OKRED+Job_Reason+bcolors.ENDC])
    
            if not Job_Dependency == "(null)":
                x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Job Dependency"+bcolors.ENDC,Job_Dependency])
    
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Running Time"+bcolors.ENDC, Job_Running_time])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Total Time"+bcolors.ENDC, Job_Total_Time])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Submit Host"+bcolors.ENDC, Sub_Host])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Submit Time"+bcolors.ENDC, Sub_Time])
            x.add_row([divider,divider])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Job Resource"+bcolors.ENDC, "Node={}".format(Job_NumNodes)])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"NumCPUs"+bcolors.ENDC,Job_NumCPUs])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"CPUsPerTask"+bcolors.ENDC,Job_CPUsPerTask])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"CPUsPerNode"+bcolors.ENDC,Job_MinCPUsNode])
            if "MinMemoryCPU" in job_info:
                x.add_row([bcolors.OKBLUE+bcolors.BOLD+"MemoryPerCore"+bcolors.ENDC,Job_MemoryPerCpu])
    
            if "MinMemoryNode" in job_info:
                x.add_row([bcolors.OKBLUE+bcolors.BOLD+"MemoryPerNode"+bcolors.ENDC,Job_MinMemoryNode])
    
            if not Job_Gres == "(null)":
                x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Gres"+bcolors.ENDC,Job_Gres])
    
            if not Job_Constraint == "(null)":
                x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Constraint"+Job_Constraint])

            x.add_row([divider,divider])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Job Working Dir"+bcolors.ENDC,Job_WorkDir])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Job Command File/Script"+bcolors.ENDC,Job_Command])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Job Output File"+bcolors.ENDC,Job_Outfile])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Job Error File"+bcolors.ENDC,Job_Errfile])
            print(x)
            sys.exit(0)
        except subprocess.CalledProcessError as error:
            print("ShowJob  subprocess command threw an error. {}  error code {}".format( error.returncode, error.output))
            print("Command is {}".format(command))
            sys.exit(1)
################################################

    @classmethod
    def Check_User_Limit (self,userName, fullUserName ):

        Total_NumNodes=0
        Total_NumCPUs=0
        Num_Submitted_JOB=0
        Num_Running_JOB=0
        Num_Pending_JOB=0

        if debug: print("Check_User_Limit userid={} username={}".format(userName,fullUserName))
    
        try:
            slurm_command=subprocess.Popen(self.SQUEUE+ " --long -u %s | grep %s |  awk {'print $1'} | wc -l" % (userName,userName), shell=True, stdout=subprocess.PIPE)
            Num_Submitted_JOB=slurm_command.communicate()[0].decode('utf-8').rstrip('\n')
            if debug: print("Num_Submitted_JOB is ",Num_Submitted_JOB)
    
            slurm_command=subprocess.Popen(self.SQUEUE+ " --long -u %s |  grep RUNNING | awk {'print $1'} | wc -l" % (userName), shell=True, stdout=subprocess.PIPE)
            Num_Running_JOB=slurm_command.communicate()[0].decode('utf-8').rstrip('\n')

            slurm_command=subprocess.Popen(self.SQUEUE + " --long -u %s | grep PENDING | awk {'print $1'} | wc -l" % (userName), shell=True, stdout=subprocess.PIPE)
            Num_Pending_JOB=slurm_command.communicate()[0].decode('utf-8').rstrip('\n')

            slurm_command=subprocess.Popen(self.SQUEUE+ " --noheader --format=%s --user=%s |  grep RUNNING | awk -F':' {'print $1'}" % ("%C:%T:%P",userName), shell=True, stdout=subprocess.PIPE)
            Running_JOB_list=slurm_command.communicate()[0].decode('utf-8').rstrip('\n')
    
            for NumCPUs in Running_JOB_list.splitlines():
                Total_NumCPUs=int(NumCPUs)+Total_NumCPUs

            x = PrettyTable()
            #x.field_names=[""]
            title=bcolors.OKBLUE+bcolors.BOLD+"MY JOB SUMMARY"+bcolors.ENDC +"                                                    "
            print(title)
            col1="Summary"
            col2="Value"
            x.field_names=[col1,col2]
            x.align[col1]="l"
            x.align[col2]="l"
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"Cluster"+bcolors.ENDC,bcolors.OKBLUE+bcolors.BOLD+"{}".format(self.SITE)+bcolors.ENDC])
            x.add_row([bcolors.OKBLUE+bcolors.BOLD+"User Name"+bcolors.ENDC,bcolors.OKBLUE+bcolors.BOLD+"{}".format(fullUserName)+bcolors.ENDC])
            x.add_row([bcolors.BOLD+"Num of Submitted Jobs"+bcolors.ENDC,"{}".format(Num_Submitted_JOB)])
            x.add_row([bcolors.BOLD+"Num of Running Job"+bcolors.ENDC,"{}".format(Num_Running_JOB)])
            x.add_row([bcolors.BOLD+"Num of Pending Jobs"+bcolors.ENDC,"{}".format(Num_Pending_JOB )])
            x.add_row([bcolors.BOLD+"Num of CPU Cores"+bcolors.ENDC,"{}".format(Total_NumCPUs)])
            print(x)
        except subprocess.CalledProcessError as error:
            print("Check_User_Limit  subprocess command threw an error. error code", error.returncode, error.output)
            sys.exit(1)

    ################################################
    @classmethod
    def decodeJobReason(self,Job_Reason, Job_State, Node_List):
        '''
        turns the Job Reason field from slurm into something meaningful for user, Node list is array of nodes
        used to impove output
        returns a string to be used in display
        '''
        Last_column=""
        if Job_Reason == "None" and Job_State == "RUNNING":
            if len(Node_List) >= 24:
                Last_column=Node_List[0:20]+"..."
            else:
                Last_column=Node_List

        if Job_Reason == "None" and Job_State == "PENDING":
            Last_column=""
        if Job_Reason == "InvalidQOS" and Job_State == "PENDING":
            Last_column=bcolors.OKRED+"Preempting Low-QOS Job"+bcolors.ENDC
        if Job_Reason == "Resources":
            Last_column=bcolors.OKRED+"NO Avail Resource"+bcolors.ENDC
        if "NodeNotAvail" in Job_Reason:
            Last_column=bcolors.OKRED+"NO Avail Resource" +bcolors.ENDC
        if Job_Reason == "Priority":
            Last_column=bcolors.OKRED+"NO Avail Resource"+bcolors.ENDC
        if Job_Reason == "Dependency":
            Last_column="Depend on Other Jobs"+bcolors.ENDC
        if "QOS" in Job_Reason and "Limit" in Job_Reason:
            Last_column=bcolors.OKRED+"Reach User Job Limit"+bcolors.ENDC
        if "Mem" in Job_Reason:
            Last_column=bcolors.OKRED+"Reach User Job Limit (Mem)"+bcolors.ENDC
        if "Cpu" in Job_Reason:
            Last_column=bcolors.OKRED+"Reach User Job Limit (CPU)"+bcolors.ENDC
        if Job_Reason == "AssocGrpCPUMinsLimit":
            Last_column=bcolors.OKRED+"Insufficient Credit"+bcolors.ENDC
        if Job_Reason == "DependencyNeverSatisfied":
            Last_column=bcolors.OKRED+"Dependency Cant Achieve"+bcolors.ENDC
        return Last_column


    ################################################
    @classmethod
    def Show_Job_List (self,userName,  JOB_TYPE, display_detail):
        print("*****************")
        print(bcolors.OKBLUE+bcolors.BOLD+"Job Details on {}".format(self.SITE)+bcolors.ENDC)
        print("*****************")
        x = PrettyTable()
        normal_field_names=["JOBID","JOB NAME","Project","QOS","STATE","RUNNING TIME","TOTAL TIME","NO OF NODES","DETAILS"]
        root_field_names=["ID", "USER", "Project", "JOBNAME", "PARTITION", "QOS", "STATE", "RUNNING TIME", "TOTAL TIME", "NO OF NODES", "DETAILS"]
        if not display_detail:
            USER_STRING="-u "+userName
            x.field_names=["JOBID","JOB NAME","Project","QOS","STATE","RUNNING TIME","TOTAL TIME","NO OF NODES","DETAILS"]
        else:  #display_detail:
            x.field_names=["ID", "USER", "Project", "JOBNAME", "PARTITION", "QOS", "STATE", "RUNNING TIME", "TOTAL TIME", "NO OF NODES", "DETAILS"]
            if userName == "":
                USER_STRING=" "
            else:
                USER_STRING="-u "+userName


#   slurm_command=subprocess.Popen("/usr/local/slurm/latest/bin/squeue %s --noheader -S u --format=%s | grep \"%s\" %s" % (USER_STRING,"%A\|%j\|%T\|%M\|%l\|%D\|%N\|%r\|%u\|%P\|%q\|%a",SITE+"-.*-c6",JOB_TYPE_STRING), shell=True, stdout=subprocess.PIPE)
    #command= SQUEUE+ " {}  --noheader -S u --format={} {} ".format(USER_STRING,"%A\|%j\|%T\|%M\|%l\|%D\|%N\|%r\|%u\|%P\|%q\|%a",JOB_TYPE_STRING)
    #command="squeue %s --noheader -S u --format=%s | grep \"%s\" %s" % (USER_STRING,"%A\|%j\|%T\|%M\|%l\|%D\|%N\|%r\|%u\|%P\|%q\|%a",SITE+"-.*-c6",JOB_TYPE_STRING)
        if debug:
            print("Show_Job_List userName={} JOB_TYPE={} display_detail={} USER_STRING={}".format(userName,JOB_TYPE,display_detail,USER_STRING))
        command= self.SQUEUE+ " %s --noheader -S u --format=\"%s\" %s "% (USER_STRING,"%A|%j|%T|%M|%l|%D|%N|%r|%u|%P|%q|%a",JOB_TYPE)
        
        if debug:
            print("show_job_list: Command is {}".format(command))


        JOB_list=subprocess.check_output(command,shell=True  ).decode('UTF-8')
        
        for entry in JOB_list.splitlines():
            if debug: print("show_job entry is {}".format(entry))
            JobID=entry.split('|')[0]
            Job_Name=entry.split('|')[1][0:9]
            Job_State=entry.split('|')[2]
            Job_Running_time=entry.split('|')[3][:-3]
            Job_Total_Time=entry.split('|')[4][:-3]
            Num_Node=entry.split('|')[5]
            Node_List=entry.split('|')[6]
            Job_Reason=entry.split('|')[7][0:24]
            userName=entry.split('|')[8][0:14]
            Partition=entry.split('|')[9]
            QoS=entry.split('|')[10]
            Project=entry.split('|')[11]
            Last_column=self.decodeJobReason(Job_Reason, Job_State, Node_List)
            if not display_detail: # == 0:  # Non-root user
                if Job_State == "RUNNING":
                    #print "\x1b[96m%-7s\x1b[0m %15s %11s %11s \x1b[1;32m%10s\x1b[0m %9s %9s %6s %27s" % (JobID,Job_Name,Project,QoS,"Running",Job_Running_time,Job_Total_Time,Num_Node,Last_column)
                    x.add_row([ bcolors.OKGREEN+JobID+ bcolors.ENDC, Job_Name, Project, QoS, bcolors.OKGREEN+"Running"+bcolors.ENDC,Job_Running_time,Job_Total_Time,Num_Node,Last_column])

                elif Job_State == "PENDING":
                    #print "\x1b[96m%-7s\x1b[0m %15s %11s %11s \x1b[1;31m%10s\x1b[0m %9s %9s %6s \x1b[0;31m%27s\x1b[0m" % (JobID,Job_Name,Project,QoS,"Pending",Job_Running_time,Job_Total_Time,Num_Node,Last_column)
                    x.add_row([ bcolors.OKGREEN+JobID+ bcolors.ENDC, Job_Name, Project, QoS, bcolors.OKRED+"PENDING"+bcolors.ENDC,Job_Running_time,Job_Total_Time,Num_Node,Last_column])
                else:
                    x.add_row([ bcolors.OKGREEN+JobID+ bcolors.ENDC, Job_Name, Project, QoS, bcolors.OKRED+Job_State+bcolors.ENDC,Job_Running_time,Job_Total_Time,Num_Node,Last_column])
                

            else: #if display_detail == 1: # Root user
                #print("SIMON {} {}".format(JobID, Job_State))
                if Job_State == "RUNNING":
                    #print "\x1b[96m%-7s\x1b[0m %15s %11s %12s %12s %11s \x1b[0;32m%10s\x1b[0m %9s %9s %6s %27s" %(JobID,USERID,Project,Job_Name,Partition,QoS,"Running",Job_Running_time,Job_Total_Time,Num_Node,Last_column)
                    x.add_row([ bcolors.OKGREEN+JobID+ bcolors.ENDC, userName, Project, Job_Name, Partition, QoS, bcolors.OKGREEN+"Running"+bcolors.ENDC,Job_Running_time,Job_Total_Time,Num_Node,Last_column])

                elif Job_State == "PENDING":
                    #print "\x1b[96m%-7s\x1b[0m %15s %11s %12s %12s %11s \x1b[0;31m%10s\x1b[0m %9s %9s %6s \x1b[0;31m%27s\x1b[0m"
                    # %(JobID,USERID,Project,Job_Name,Partition,QoS,"Pending",Job_Running_time,Job_Total_Time,Num_Node,Last_column)
                    #print("SIMON ADD PENDING ROW")
                    x.add_row([ bcolors.OKGREEN+JobID+ bcolors.ENDC,
                            userName, Project, Job_Name, Partition,
                            QoS,
                            bcolors.OKRED+"Pending"+bcolors.ENDC,
                            Job_Running_time,
                            Job_Total_Time,Num_Node,Last_column])
                else:
                    x.add_row([ bcolors.OKGREEN+JobID+ bcolors.ENDC,
                            userName, Project, Job_Name, Partition,
                            QoS,
                            bcolors.OKRED+Job_State+bcolors.ENDC,
                            Job_Running_time,
                            Job_Total_Time,Num_Node,Last_column])



        print(x)
        #print("End Show_Job_List")

################################################
    @classmethod
    def getFullUserName(cls,userName):
        '''
            returns full username of username, as determined by 'finger'
        '''
        try:
            system_command=subprocess.Popen("/bin/finger {} | grep Name: ".format(userName)+ " | awk -F ':' {'print $3'}", shell=True, stdout=subprocess.PIPE)
            #print("Command is {}".format(system_command))
            fullUserName=system_command.communicate()[0].decode('utf-8').strip()
            #print("Username={}".format(fullUserName))
            return fullUserName
        except subprocess.CalledProcessError as error:
            print("getFullUsername  subprocess command threw an error. error code", error.returncode, error.output)
            sys.exit(1)

    ################################################
    @classmethod
    def main(cls,argv):

        JOB_TYPE=""
        CHECK_ONE_USER=False
        CHECK_ONE_JOB=False
        CHECK_ONE_TYPE=False
        CHECK_ALL=False

        cls.find_slurm_paths()
        cls.set_site()

        try:
            #   Check_Single_Job("75228")
            userName=getpass.getuser()
            fullUserName=cls.getFullUserName(userName)
            if debug:
                print("main: Username={} argv={}".format(fullUserName,argv))
            if userName == "root" or userName=="smichnow":
                display_detail=True #root user
                if len(sys.argv) != 1 :
                    if debug:
                      print("Testing \"{}\' in PartitionList {}".format(sys.argv[1],cls.PartitionList))
                    if sys.argv[1] in cls.PartitionList:
                        SHOW_BOTH_CLUSTER_FLAG=True
                        JOB_TYPE="--partition={}".format(sys.argv[1])
                        CHECK_ONE_TYPE=True
                    elif sys.argv[1].isdigit():
                        CHECK_ONE_JOB=True
                        cls.Check_Single_Job(Job_ID=sys.argv[1])
                    else:
                        CHECK_ONE_USER=True

                if len(sys.argv) == 1 :
                    CHECK_ALL=True
            else: #not root
                display_detail=False #normal user
                if len(sys.argv) != 1 :
                    if sys.argv[1] in cls.PartitionList:
                        JOB_TYPE="--partition={}".format(sys.argv[1])
                        #JOB_TYPE=sys.argv[1]
                        CHECK_ONE_TYPE=True
                        SHOW_BOTH_CLUSTER_FLAG=True
                    elif sys.argv[1].isdigit():
                        CHECK_ONE_JOB=True
                        cls.Check_Single_Job(sys.argv[1])

                if len(sys.argv) == 1 :
                    CHECK_ALL=True
    

            if not display_detail : # User
                if CHECK_ONE_TYPE:
                    cls.Check_User_Limit (userName,fullUserName)
                    cls.Show_Job_List (userName,  JOB_TYPE, display_detail)
                    print("")
                    print("")
                    #Check_User_Limit (USERID,USER_NAME)
                    #Show_Job_List (USERID,  JOB_TYPE, display_detail)
                    print("")
                    print("")

                else :
                    if debug: print("main: before cls.Check_User_Limit {} {} ".format(userName,fullUserName))
                    cls.Check_User_Limit (userName,fullUserName)
                    cls.Show_Job_List (userName,  "", display_detail)
                    print("")
                    print("")
                    #Check_User_Limit (USERID,USER_NAME)
                    #Show_Job_List (USERID,  "", display_detail)
                    print("")
                    print("")

            else: #if display_detail: # Root
                if CHECK_ONE_USER:
                    userName=sys.argv[1]
                    fullUserName=cls.getFullUserName(userName)
                    cls.Check_User_Limit (userName,fullUserName)
                    cls.Show_Job_List (userName,  "", display_detail)
                    print("")
                    print("")
                else:
                    cls.Show_Job_List ("",  JOB_TYPE, display_detail)
                    #Show_Job_List ("", "", display_detail)
        except subprocess.CalledProcessError as error:
            print("Check_User_Limit  subprocess command threw an error. error code", error.returncode, error.output)
            sys.exit(1)

################################################
def main(argv):
    show_job.main(argv[1:])

if __name__ == '__main__':
    main(sys.argv[1:])


