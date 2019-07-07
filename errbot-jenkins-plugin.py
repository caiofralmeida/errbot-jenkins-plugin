from errbot import BotPlugin, botcmd, arg_botcmd, webhook
from requests.exceptions import HTTPError
from jenkins_service import JenkinsService

class ErrbotJenkinsPlugin(BotPlugin):

    def get_configuration_template(self):
        return {
            'JENKINS_TOKEN': '',
            'JENKINS_USERNAME': '',
            'JENKINS_URL': '',
        }
    
    def callback_message(self, message):
        if not self.config:
            return "Please configure this plugin passing the Jenkins credentials."

    @arg_botcmd('pattern', type=str)
    def jenkins_search_job(self, message, pattern=None):
        jenkins_service = JenkinsService(self.config)
        yield "Ok, vou procurar para você..."

        jobs = jenkins_service.search_job_by_name(pattern)

        if len(jobs) == 0:
            yield "Infelizmente não encontrei nenhum job, você pode passar uma expressão regular como exemplo: `!jenkins search job *corp*`"
            return

        if len(jobs) == 1:
            self['user'] = {'selected_job': jobs[0]}
            yield "Encontrei o job `{}`, o que deseja fazer com ele?".format(jobs[0]['name'])
            return

        self['user'] = {'job_list': jobs}
        
        yield "Encontrei mais de um job, escolha com qual deseja atuar: Rode !jenkins select job <id>"
        for id, job in enumerate(jobs):
            yield str(id + 1) + " - " + job['name'] + "\n"


    @arg_botcmd('number', type=str)
    def jenkins_select_job(self, message, number):
        job = self['user']['job_list'][int(number) - 1]
        
        self['user'] = {'selected_job': job}
        yield "O que deseja fazer com o job {}?".format(job['name'])


    @arg_botcmd('--job-name', type=str, unpack_args=False)
    def jenkins_show_job_info(self, message, args):
        jenkins_service = JenkinsService(self.config)

        yield "Beleza {}, só um minuto..:beer:".format(message.frm.nick)
        
        if not args.job_name:
            args.job_name = self['user']['selected_job']['name']

        job_info = jenkins_service.job_info(args.job_name)
        yield "\n"
        yield "name: {}\n".format(job_info['name'])
        yield "description: {}\n".format(job_info['description'])
        yield "url: {}\n".format(job_info['url'])
        if job_info['lastBuild']:
            last_build = job_info['lastBuild']
            yield "last build: ({}) {}\n".format(last_build['number'], last_build['url'])


    @arg_botcmd('--job-name', type=str, unpack_args=False)
    @arg_botcmd('--parameters', type=str, unpack_args=False)
    def jenkins_build_job(self, message, args):
        jenkins_service = JenkinsService(self.config)
        
        if not args.job_name:
            args.job_name = self['user']['selected_job']['name']
        
        try:
            parameters = {}
            if args.parameters:
                for param_pairs in args.parameters.split(','):
                    param = param_pairs.split('=')
                    parameters[param[0]] = param[1]
            
            sequence_id = jenkins_service.build_job(args.job_name, parameters)
            job_info = jenkins_service.job_info(args.job_name)
            build_number = int(job_info['lastBuild']['number']) + 1
            
            return "build sendo executado em {}{}/".format(job_info['url'], build_number)
        except HTTPError as e:
            if e.response.status_code == 400:
                return "Esse job depende de parametros para ser executado, tente !jenkins build job --parameters PARAM1=value,PARAM2=value"