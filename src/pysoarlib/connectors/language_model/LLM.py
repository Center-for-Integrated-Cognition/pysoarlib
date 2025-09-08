""" 
    Handles lm-requests commands on the output link
    constructs prompts from templates and gets response from language model 
"""

import json
from pysoarlib.connectors.language_model.LMResponse import LMResponse
#from LanguageModelConnector.LMResult import LMResult
from pysoarlib.connectors.language_model.LMResult import LMResult


import os
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAI
import numpy as np
import openai

#TODO disable for now
#from langchain_anthropic import ChatAnthropic

#optional for langsmith tracing/logging
# try:
#     from langchain.callbacks import LangChainTracer
#     from langsmith import Client
# except ImportError:
#     pass
meta_template = "?examples?world-context?soar-context?history-context?repair-prompt?prompt?output"

class LLM:

    def __init__(self, world_connector, templates_root, temperature=0, model="gpt-4", api="langchain"):
        #self.connector = connector
        self.response = None
        self.model = model
        #print(model)
        self.temperature = temperature
        self.world_connector = world_connector
        self.templates_root = templates_root
        self.api = api
        self.command_history = ""
        self.test_mode = False # This can be set to True to inhibit printouts

        """ Calculate path to templates folder """
        if not self.templates_root:
            self.templates_root = "templates/"
            dirname = os.path.dirname(__file__)
            self.templates_root = os.path.join(dirname, self.templates_root)
        else:
            if not self.templates_root.endswith("/"):
                self.templates_root = self.templates_root + "/"


    def get_str_from_file(self, filename):
        """ strip text from file given filename
        """
        lines = []
        with open(filename) as f:
            lines = f.read().splitlines()
        output = ""
        for line in lines:
            output += line + "\n"
        return output.rstrip();

    def get_config(self, type):
        """
        get template from folder for prompt given type
        """
        cwd = os.getcwd()
        file = self.templates_root + type + "/config.json"
        path = os.path.join(cwd, file)
        
        with open(path) as file:
            config = json.load(file)

        return config
    
    def get_llm_template(self, type):
        """
        get template from folder for prompt given type
        """
        cwd = os.getcwd()
        file = self.templates_root + "llm-templates/" + type + ".json"
        path = os.path.join(cwd, file)
        with open(path) as file:
            template_config = json.load(file)

        return template_config
    
    def get_template(self, type):
        """
        get template from folder for prompt given type
        """
        cwd = os.getcwd()
        file = self.templates_root + type + "/user.txt"
        path = os.path.join(cwd, file)
        template = self.get_str_from_file(path)
        return template

    def get_system_prompt(self, type):
        """
        return system prompt template given type
        """
        cwd = os.getcwd()
        file = self.templates_root + type + "/system.txt"
        path = os.path.join(cwd, file)
        prompt = self.get_str_from_file(path)
        return prompt
    
    def get_response_type(self, type):
        """
        return response type (string, int) given template type
        """
        cwd = os.getcwd()
        file = self.templates_root + type + "/response_type.txt"
        path = os.path.join(cwd, file)
        type = self.get_str_from_file(path)

        return type

    
    def instantiate_template(self, template, arguments):
        """
        replace argument slots with given argument 
        """
        i = 1
        temp = template
        for arg in arguments:
             variable = "?argument" + str(i)
             temp= temp.replace(variable, str(arg))
             i+=1
        return temp;


    
    def construct_prompt(self, template_type, arguments):
        """
        Constructs prompt by retrieving template and instantiating
        returns user prompt and system prompt 
        """
        prompt = ""

        template = self.get_template(template_type)
        #print(template)
        prompt = self.instantiate_template(template, arguments)
        #print(prompt)
        system_prompt = self.get_system_prompt(template_type)
        #print(system_prompt)
        
        return prompt, system_prompt


    def prompt_llm_langchain_json(self, sentence, prompt, system_prompt, query, response_type, sequence_number):
        temperature = self.temperature
        model = "gpt-4o-2024-08-06" #"gpt-4o-2024-05-13"#"gpt-4o"
        #llm = ChatOpenAI(model_name=model, temperature=temperature, response_format="json")
        llm = ChatOpenAI(model_name=model, temperature=temperature).bind(response_format={"type": "json_object"})
        #llm = ChatOpenAI(model_name=model, temperature=temperature).bind(response_format: {"type": "json_object"})

        system_input = system_prompt
        user_input = prompt

        message = [
            ("system", system_input),
            ("human", user_input),
        ]

        print("System prompt:" + system_input)
        print("User prompt:" + user_input)

        response = llm.invoke(message)

        #print("Response:" + response.content)
        content = response.content
        json_object = json.loads(content)
        print(json_object)
        results = []
        result = LMResult(json_object, response_type, 1.0, 1)
        results.append(result)
        if sentence:
            self.command_history = self.command_history + "\nInput:" + sentence + "\n"
            self.command_history = self.command_history + "World update: " + str(json_object).replace("desired", "relation")
        return LMResponse(query, results,sequence_number)
    


    def prompt_llm_langchain(self, prompt, system_prompt):
        """
        prompt llm using supplied prompts
        return response
        """

        temperature = self.temperature
        model = self.model
        
        llm = ChatOpenAI(model_name=model, temperature=temperature)
        
        system_input = system_prompt
        user_input = prompt

        message = [
            ("system", system_input),
            ("human", user_input),
        ]

        print("System prompt:" + system_input)
        print("User prompt:" + user_input)

        response = llm.invoke(message)

        #print("Response:" + response.content)

        return response
    

    def prompt_llm_langchain_anthropic(self, prompt, system_prompt):
        """
        prompt llm using supplied prompts
        return response
        """

        temperature = self.temperature
        
        llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=temperature, max_tokens=10,timeout=None,max_retries=1)
        
        system_input = system_prompt
        user_input = prompt

        message = [
            ("system", system_input),
            ("human", user_input),
        ]

        print("System prompt:" + system_input)
        print("User prompt:" + user_input)

        response = llm.invoke(message)

        #print(response)

        print("Anthropic Response:" + response.content)
        return response
    
    def prompt_llm_langchain_o1(self, prompt, system_prompt):
        """
        prompt llm using supplied prompts
        return response
        """
        client = openai.OpenAI()
        temperature = self.temperature
        model = "o1-preview"
        
        #llm = ChatOpenAI(model_name=model, temperature=temperature)
        
        # system_input = system_prompt
        # user_input = prompt

        # message = [
        #     ("system", system_input),
        #     ("human", user_input),
        # ]

        # print("System prompt:" + system_input)
        user_input = system_prompt + " " + prompt
        print("User prompt:" + user_input)

        #response = llm.invoke(message)

        messages = [{"role": "user", "content": user_input}]
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        print(response)
        final_response = response.choices[0].message.content

        print("Response: " + final_response)

        return response
    

    def prompt_llm_langchain_multi_response_completion(self, prompt, system_prompt, num_results):
        """
        prompt llm using supplied prompts
        return response
        """

        temperature = self.temperature
        #model = self.model
        model = "gpt-3.5-turbo-instruct"
        if num_results == 1:
            llm = OpenAI(model_name=model, temperature=temperature) #.bind(logprobs=True) #don't need top logprobs for one result
            #llm = OpenAI(model_name=model, temperature=temperature,logprobs=True) #don't need top logprobs for one result
        else:
            #llm = OpenAI(model_name=model, temperature=temperature).bind(logprobs=True).bind(top_logprobs=num_results)
            llm = OpenAI(model_name=model, temperature=temperature,logprobs=True,top_logprobs=num_results)
        
        system_input = system_prompt
        user_input = system_input + prompt

        # message = [
        #     ("system", system_input),
        #     ("human", user_input),
        # ]

        #print("System prompt:" + system_input)
        print("User prompt:" + user_input)

        response = llm.invoke(user_input)

        #print("Response:" + response.content)
        print(response)
        return response
    
    def prompt_llm_langchain_multi_response(self, prompt, system_prompt, num_results):
        """
        prompt llm using supplied prompts
        return response
        """

        temperature = self.temperature
        model = self.model
        #model = "gpt-3.5-turbo-instruct"
        if num_results == 1:
            llm = ChatOpenAI(model_name=model, temperature=temperature).bind(logprobs=True) #don't need top logprobs for one result
        else:
            llm = ChatOpenAI(model_name=model, temperature=temperature).bind(logprobs=True).bind(top_logprobs=num_results)
        
        system_input = system_prompt
        user_input = prompt

        message = [
            ("system", system_input),
            ("human", user_input),
        ]

        print("System prompt:" + system_input)
        print("User prompt:" + user_input)

        response = llm.invoke(message)

        #print("Response:" + response.content)

        return response
    

    def get_primary_result(self, llm_response, response_type):
        logprob = llm_response.response_metadata['logprobs']['content'][0]['logprob']
        prob = np.exp(float(logprob))
        return LMResult(llm_response.content, response_type, prob, 1)


    def complete_toplogprob_generation(self, llm_response, response_type, prompt, system_prompt):
        results = []
        #first results
        results.append(self.get_primary_result(llm_response, response_type))

        top_logprobs = llm_response.response_metadata
        top = top_logprobs['logprobs']['content'][0]['top_logprobs']
        order = 1
        for result in top:
            if order == 1: #skip first response
                order = order + 1
                continue
            logprob = result['logprob']
            content = result['token']
            prob = np.exp(float(logprob))
            #print("new_response:")
            new_response = self.prompt_llm_langchain_multi_response_completion(prompt+"\nResponse:"+content, system_prompt, 1)
            #print(new_response)
            #results.append(LMResult(content + new_response.content, response_type, prob, order))
            results.append(LMResult(content + new_response, response_type, prob, order))
            order = order + 1

        return results


    def soar_identifier_to_json(self, soar_id):
        json_object = {}

        for index in range(soar_id.GetNumberChildren()):
            wme = soar_id.GetChild(index)
            attr = wme.GetAttribute()
            value_type = wme.GetValueType()

            if value_type == "int":
                # Convert to int and get the value
                int_value = wme.ConvertToIntElement().GetValue()
                processed_value = int_value
            elif value_type == "double":
                # Convert to float and get the value
                float_value = wme.ConvertToFloatElement().GetValue()
                processed_value = float_value
            elif value_type == "string":
                #check for boolean and nil values
                str_value = wme.GetValueAsString()
                if str_value.lower() == "true":
                    processed_value = True
                elif str_value.lower() == "false":
                    processed_value = False
                elif str_value.lower() == 'nil':
                    processed_value = None
                else:
                    processed_value = str_value             
            elif value_type == "id":
                # Convert to identifier and recurse
                child_id = wme.ConvertToIdentifier()
                processed_value = self.soar_identifier_to_json(child_id)
            else:
                # For other types, get string representation
                processed_value = wme.GetValueAsString()
            
            # Check if the attribute already exists in json_object
            if attr in json_object:
                # If it's already a list, append to it
                if isinstance(json_object[attr], list):
                    json_object[attr].append(processed_value)
                else:
                    # Convert existing value to a list
                    json_object[attr] = [json_object[attr], processed_value]
            else:
                # First occurrence of this attribute
                json_object[attr] = processed_value
        return json_object
    
    def parse_user_question_mode_a(self, query, type, arguments):
        soar_context = arguments[1]
        #json_context = self.soar_to_json(soar_context)
        json_context = self.soar_identifier_to_json(soar_context)
        
        # print("json")
        # print(json_context)
        arguments[1] = json.dumps(json_context)
        prompt, system_prompt = self.construct_prompt(type, arguments)
        response_type = self.get_response_type(type)

        number_responses = 1
        results = []

        llm_response = self.prompt_llm_langchain_multi_response(prompt, system_prompt, number_responses)
        print("initial response:" + llm_response.content)

        #logprob = llm_response.response_metadata['logprobs']['content'][0]['logprob']
        #prob = np.exp(float(logprob))
        result = LMResult(llm_response.content, response_type, 0.8, 1)
        results.append(result)
        lmr = LMResponse(query, results)
        self.response = lmr
        return self.response

    def parse_user_question_mode_b(self, query, type, arguments):
        argument_count = len(arguments)
        # if two arguments using json context
        if argument_count == 2:
            soar_context = arguments[1]
            #json_context = self.soar_to_json(soar_context)
            json_context = self.soar_identifier_to_json(soar_context)
            arguments[1] = json.dumps(json_context)
        
        prompt, system_prompt = self.construct_prompt(type, arguments)
        response_type = self.get_response_type(type)

        # number_responses = 1
        # results = []

        #llm_response = self.prompt_llm_langchain_multi_response(prompt, system_prompt, number_responses)
        lmr = self.prompt_llm_langchain_json("", prompt, system_prompt, query, response_type)
        #lmr = LMResponse(query, results)
        self.response = lmr
        return self.response;
    

    def parse_request(self, query, type, arguments, sequence_number):
        """
        handle LLM request by constructing prompt and getting response from LLM
        return LMResponse with response
        """
        

        number_responses = 5 #how to set, with arguments or seperate field? seperate field better...
        results = []

        if type == "user-question-mode-a":
            return self.parse_user_question_mode_a(query, type, arguments)
        

        if "user-question-mode-b" in type:
            return self.parse_user_question_mode_b(query, type, arguments)

        if "context-history-desireds" in type or "sentence-history-desireds" in type or "sentence-desireds-sequence" in type:
            arguments.append(self.command_history)

        prompt, system_prompt = self.construct_prompt(type, arguments)
        response_type = self.get_response_type(type)

        if "context-history-desireds" in type:
            json_context = self.world_connector.get_json_world_representation()
            json_string = json.dumps(json_context, indent=4)
            prompt= prompt.replace("?context", json_string)

        #json based code for desireds
        
        if response_type == "json":
            #hard coding for now
            lmr = self.prompt_llm_langchain_json(arguments[0], prompt, system_prompt, query, response_type, sequence_number)
            #lmr = LMResponse(query, results)
            self.response = lmr
            return self.response;


        #right now uses langchain... 

        if self.api == "langchain":
            llm_response = self.prompt_llm_langchain_multi_response(prompt, system_prompt, number_responses)
        #openai 01
        elif self.api == "o1":
            llm_response = self.prompt_llm_langchain_o1(prompt, system_prompt)
            prob = 1.0 #no logprobs for o1 yet
            content = llm_response.choices[0].message.content
            result = LMResult(content, response_type, prob, 1)
            results.append(result)
            lmr = LMResponse(query, results, sequence_number)
            self.response = lmr
            return self.response;

        print("initial response:" + llm_response.content)
        #TODO need to adapt STARS joining for multi word response
        if number_responses == 1:
            logprob = llm_response.response_metadata['logprobs']['content'][0]['logprob']
            prob = np.exp(float(logprob))
            result = LMResult(llm_response.content, response_type, prob, 1)
            results.append(result)
        else:
            top_logprobs = llm_response.response_metadata
            complete_generation = False
            if int(top_logprobs['token_usage']['completion_tokens']) > 0:
                complete_generation = True
                results = self.complete_toplogprob_generation(llm_response, response_type, prompt, system_prompt)
            else:
                top = top_logprobs['logprobs']['content'][0]['top_logprobs']
                order = 1
                for result in top:
                    logprob = result['logprob']
                    content = result['token']
                    prob = np.exp(float(logprob))
                    result = LMResult(content, response_type, prob, order)
                    results.append(result)
                    order = order + 1

        #get response from anthropic
        #TODO disable for now
        # anthropic_response = self.prompt_llm_langchain_anthropic(prompt, system_prompt)
        # prob = 0.5 #no logprobs for anthropic yet
        # content = anthropic_response.content

        # #only add result if unique
        # add_new_result = True
        # for result in results:
        #     if result.response == content:
        #         add_new_result = False 
        # if add_new_result:
        #     result = LMResult(content, response_type, prob, 6)
        #     results.append(result)
            
        for result in results:
            print("Response: " + result.response)
        
        lmr = LMResponse(query, results, sequence_number)
        self.response = lmr

        return self.response;


#################################
    def parse_request_new(self, query, type, arguments, sequence_number):
        """
        handle LLM request by constructing prompt and getting response from LLM
        return LMResponse with response
        """
        config = self.get_config(type)        

        number_responses = config["number-of-responses"] #how to set, with arguments or seperate field? seperate field better...
        results = []

        if config["append-history"]:
            arguments.append(self.command_history)

        if type == "user-question-mode-a":
            return self.parse_user_question_mode_a(query, type, arguments)

        if "user-question-mode-b" in type:
            return self.parse_user_question_mode_b(query, type, arguments)    

        prompt, system_prompt = self.construct_prompt(type, arguments)
        response_type = self.get_response_type(type)

        if config["use-world-context"]:
            json_context = self.world_connector.get_json_world_representation()
            json_string = json.dumps(json_context, indent=4)
            prompt= prompt.replace("?context", json_string)
        
        if config["response-type"] == "json":
            #hard coding for now
            lmr = self.prompt_llm_langchain_json(arguments[0], prompt, system_prompt, query, response_type, sequence_number)
            self.response = lmr
            return self.response;

        #right now uses langchain... 
        #self.api = "o1"
        if self.api == "langchain":
            llm_response = self.prompt_llm_langchain_multi_response(prompt, system_prompt, number_responses)
        #openai 01
        elif self.api == "o1":
            llm_response = self.prompt_llm_langchain_o1(prompt, system_prompt)
            prob = 1.0 #no logprobs for o1 yet
            content = llm_response.choices[0].message.content
            result = LMResult(content, response_type, prob, 1)
            results.append(result)
            lmr = LMResponse(query, results, sequence_number)
            self.response = lmr
            return self.response;

        print("initial response:" + llm_response.content)
        #TODO need to adapt STARS joining for multi word response
        if number_responses == 1:
            logprob = llm_response.response_metadata['logprobs']['content'][0]['logprob']
            prob = np.exp(float(logprob))
            result = LMResult(llm_response.content, response_type, prob, 1)
            results.append(result)
        else:
            top_logprobs = llm_response.response_metadata
            complete_generation = False
            if int(top_logprobs['token_usage']['completion_tokens']) > 0:
                complete_generation = True
                results = self.complete_toplogprob_generation(llm_response, response_type, prompt, system_prompt)
            else:
                top = top_logprobs['logprobs']['content'][0]['top_logprobs']
                order = 1
                for result in top:
                    logprob = result['logprob']
                    content = result['token']
                    prob = np.exp(float(logprob))
                    result = LMResult(content, response_type, prob, order)
                    results.append(result)
                    order = order + 1

        #get response from anthropic
        #TODO disable for now
        # anthropic_response = self.prompt_llm_langchain_anthropic(prompt, system_prompt)
        # prob = 0.5 #no logprobs for anthropic yet
        # content = anthropic_response.content

        # #only add result if unique
        # add_new_result = True
        # for result in results:
        #     if result.response == content:
        #         add_new_result = False 
        # if add_new_result:
        #     result = LMResult(content, response_type, prob, 6)
        #     results.append(result)
            
        for result in results:
            print("Response: " + result.response)
        
        lmr = LMResponse(query, results, sequence_number)
        self.response = lmr

        return self.response;

    def get_examples(self, config):
        """
        get prompt examples from file(s) specified by config
        """
        examples = ""

        if "example-context" in config:
            cwd = os.getcwd()
            file = self.templates_root + "examples/" + config["domain"] + "/" + config["example-context"] + ".txt"
            path = os.path.join(cwd, file)

            examples += self.get_str_from_file(path) + "\n"
        
        if config["examples"] and config["domain"]:
            first = True
            for example in config["examples"]:
                #print("example:" + example)
                cwd = os.getcwd()
                file = self.templates_root + "examples/" + config["domain"] + "/" + example + ".txt"
                path = os.path.join(cwd, file)
                if not first:
                    examples += "\n"
                first = False
                examples += self.get_str_from_file(path)
        return examples
    
    def get_prompt_template(self, type):
        """
        get template from folder for prompt given type
        """
        cwd = os.getcwd()
        file = self.templates_root + "prompt-templates/" + type + ".txt"
        path = os.path.join(cwd, file)
        template = self.get_str_from_file(path)
        return template
    
    def get_output_template(self, type):
        """
        get template from folder for prompt given type
        """
        cwd = os.getcwd()
        file = self.templates_root + "output-template/" + type + ".txt"
        path = os.path.join(cwd, file)
        template = self.get_str_from_file(path)
        return template
    
    def instantiate_prompt(self, config, arguments):
        """
        retrieve prompt format and instantiate argument slots with given argument 
        """

        prompt = self.get_prompt_template(config["prompt-template"])
        
        i = 1
        for arg in arguments:
             variable = "?argument" + str(i)
             prompt= prompt.replace(variable, str(arg))
             i+=1
        return prompt;

    def get_template_system_prompt(self, type):
        """
        return system prompt template given type
        """
        cwd = os.getcwd()
        file = self.templates_root + "system-prompts/" + type + ".txt"
        path = os.path.join(cwd, file)
        prompt = self.get_str_from_file(path)
        return prompt

    def instantiate_llm_template(self, type, arguments, config, soar_state_context):
        """
        instantiate llm templates based on config
        """
        template = meta_template
        examples = self.get_examples(config)
        world_context = ""
        soar_context = ""
        history_context = ""
        repair_prompt = ""
        prompt = "\n" + self.instantiate_prompt(config, arguments)
        output = "\n" + self.get_output_template(config["output-template"])

        if config["world-context"]:
            json_context = self.world_connector.get_json_world_representation()
            world_context = "\nWorld State:\n" + json.dumps(json_context, indent=4)

        if config["soar-context"] and soar_state_context:
            json_context = self.soar_identifier_to_json(soar_state_context)
            soar_context = "\nWorld Context:\n" + json.dumps(json_context, indent=4)

        if config["history-context"]:
            history_context = self.command_history #TODO specify different ways to record history (dialog, actions, messages)

        #replace all template variables
        template = template.replace("?examples", examples)
        template = template.replace("?world-context", world_context)
        template = template.replace("?soar-context", soar_context)
        template = template.replace("?history-context", history_context)
        template = template.replace("?repair-prompt", repair_prompt)
        template = template.replace("?prompt", prompt)
        template = template.replace("?output", output)

        return template
    
    

    # def prompt_llm_langchain_multi_response(self, prompt, system_prompt, num_results):
    #     """
    #     prompt llm using supplied prompts
    #     return response
    #     """

    #     temperature = self.temperature
    #     model = self.model
    #     #model = "gpt-3.5-turbo-instruct"
    #     if num_results == 1:
    #         llm = ChatOpenAI(model_name=model, temperature=temperature).bind(logprobs=True) #don't need top logprobs for one result
    #     else:
    #         llm = ChatOpenAI(model_name=model, temperature=temperature).bind(logprobs=True).bind(top_logprobs=num_results)
        
    #     system_input = system_prompt
    #     user_input = prompt

    #     message = [
    #         ("system", system_input),
    #         ("human", user_input),
    #     ]

    #     print("System prompt:" + system_input)
    #     print("User prompt:" + user_input)

    #     response = llm.invoke(message)

    #     #print("Response:" + response.content)

    #     return response

    def prompt_langchain(self, user_prompt, system_prompt, query, config, sequence_number, dialog):
        temperature = config["temperature"]
        model = config["model"]
        num_results = config["number-of-results"]
        #more advanced models (gpt-5, o1, o3, o3-mini, etc.) cannot accept temperature setting
        print ("Model:" + model)
        if config["response-type"] == "json":
            if model == "gpt-4o" or model == "gpt-4o-2024-08-06" or model == "gpt-4.1" or model == "gpt-4.1-mini":
                print("Using model " + model + " with temperature setting")
                llm = ChatOpenAI(model_name=model, temperature=temperature).bind(response_format={"type": "json_object"})
            else:
                print("Using model " + model + " without temperature setting")
                llm = ChatOpenAI(model_name=model).bind(response_format={"type": "json_object"})
        else:
            if num_results == 1:
                if model == "gpt-4o" or model == "gpt-4o-2024-08-06" or model == "gpt-4.1" or model == "gpt-4.1-mini":
                    print("Using model" + model + " with temperature setting")
                    llm = ChatOpenAI(model_name=model, temperature=temperature) #.bind(logprobs=True) 
                else:
                    print("Using model " + model + " without temperature setting")
                    llm = ChatOpenAI(model_name=model)# reasoning_effort="low")#
            else:
                if model == "gpt-4o" or model == "gpt-4o-2024-08-06" or model == "gpt-4.1" or model == "gpt-4.1-mini":
                    print("Using model " + model + " with temperature setting")
                    llm = ChatOpenAI(model_name=model, temperature=temperature).bind(logprobs=True).bind(top_logprobs=num_results)
                else:
                    print("Using model " + model + " without temperature setting")
                    llm = ChatOpenAI(model_name=model).bind(logprobs=True).bind(top_logprobs=num_results)
                
        system_input = system_prompt
        user_input = user_prompt

        message = [
            ("system", system_input),
            ("human", user_input),
        ]

        if not self.test_mode:
            print("System prompt:")
            print(system_input)
            print("User prompt:")
            print(user_input)

        response = llm.invoke(message)

        #print(response)
        content = response.content

        
        results = []
        if config["response-type"] == "json":
            json_object = json.loads(content)
            if not self.test_mode:
                print(json.dumps(json_object, indent=4))
            
            result = LMResult(json_object, "json", 1.0, 1)
            results.append(result)

            if "dialog" in config["history-context"]:
                self.command_history = self.command_history + "\nInput:" + dialog + "\n"
            
            if "state" in config["history-context"]:
                self.command_history = self.command_history + "World update: " + str(json_object).replace("desired", "relation")
        elif num_results == 1:
            if not self.test_mode:
                print("Response:" + content)

            if "dialog" in config["history-context"]:
                self.command_history = self.command_history + "\nQuestion:" + dialog + "\n" #fix generality
                self.command_history = self.command_history + "Answer:" + content # + "\n"
            result = LMResult(content, config["response-type"], 1.0, 1) #todo fix probability access
            results.append(result)
        else: #TODO handle multi json response
            top_logprobs = response.response_metadata
            complete_generation = False
            if int(top_logprobs['token_usage']['completion_tokens']) > 0:
                complete_generation = True
                results = self.complete_toplogprob_generation(response, config["response-type"], user_input, system_prompt)
            else:
                top = top_logprobs['logprobs']['content'][0]['top_logprobs']
                order = 1
                for result in top:
                    logprob = result['logprob']
                    content = result['token']
                    prob = np.exp(float(logprob))
                    result = LMResult(content, config["response-type"], prob, order)
                    results.append(result)
                    order = order + 1
  
            #for result in results:
                #print("Response: " + result.response)
        
        return LMResponse(query, results, sequence_number)


    #def process_request(self, query, type, arguments, sequence_number, soar_state_context):
    def process_request(self, query):
        """
        handle LLM request by constructing prompt and getting response from LLM
        return LMResponse with response
        """
        template_config = self.get_llm_template(query.type)

        #Special case: multiple possible modes
        #in the future prompt llm for best way to treat (or try multiple)
        #right now simple hard coded tests
        selected_type = ""
        if "select-from-templates" in template_config:
            for template in template_config["select-from-templates"]:
                if template == "thor-question-mode-A" and query.arguments[0][-1] == "?":
                    selected_type = "thor-question-mode-A"
                if template == "thor-question-dag" and query.arguments[0][-1] == "?":
                    selected_type = "thor-question-dag"
                if template == "context-history-desireds" and query.arguments[0][-1] != "?":
                    selected_type = "context-history-desireds"
                if template == "thor-goal-dag" and query.arguments[0][-1] != "?":
                    selected_type = "thor-goal-dag"
        if selected_type:
            type = selected_type
            template_config = self.get_llm_template(selected_type)

        user_prompt = self.instantiate_llm_template(query.type, query.arguments, template_config, query.context)
        system_prompt = self.get_template_system_prompt(template_config["system-prompt"])

        
        #if config["api"] == "langchain": all langchain for now
        #todo change to just pass query
        self.response = self.prompt_langchain(user_prompt, system_prompt, query, template_config, query.sequence_number, query.arguments[0])
        return self.response;

