import jenkins
import re
import fnmatch
import json

class JenkinsService:
    def __init__(self, config):
        self.token = config['JENKINS_TOKEN']
        self.jenkins = jenkins.Jenkins(config['JENKINS_URL'],
            username=config['JENKINS_USERNAME'],
            password=self.token)
    
    def search_job_by_name(self, expression):
        job_list = []
        regex = fnmatch.translate(expression)
        pattern = re.compile(regex)
        for job in self.jenkins.get_jobs():
            if pattern.match(job['name']):
                job_list.append(job)
        return job_list
    
    def build_job(self, job_name, parameters=None):
        return self.jenkins.build_job(job_name, parameters, token=self.token)

    def job_info(self, job_name):
        return self.jenkins.get_job_info(job_name)
