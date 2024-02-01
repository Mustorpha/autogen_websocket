import autogen
from .user_proxy_webagent import UserProxyWebAgent
from .groupchatweb import GroupChatManagerWeb
import asyncio
import json

from langchain.utilities import SearchApiAPIWrapper

config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": "OPENAI-API-KEY"
    }
]
llm_config_assistant = {
    "model":"gpt-3.5-turbo",
    "temperature": 0,
    "config_list": config_list,
        "functions": [
        {
            "name": "get_info_about",
            "description": "Get a topic and return the news related to that topic. For research purposes.",
            "parameters":{
                "type": "object",
                "properties": {
                    "topic":{
                        "type": "string",
                        "description": "topic for searching",
                    },
                },
                "required":["topic"],
            },
        },
    ],
}
llm_config_writer = {
    "model":"gpt-3.5-turbo-0613",
    "temperature": 0,
    "config_list": config_list,
}


class AutogenChat():
    def __init__(self, websocket=None):
        self.websocket = websocket
        # self.chat_id = chat_id
        self.client_sent_queue = asyncio.Queue()
        # self.client_receive_queue = asyncio.Queue()

        self.advisor = autogen.AssistantAgent(
            name="advisor",
            llm_config=llm_config_assistant,
            max_consecutive_auto_reply=5,
            system_message="""You are an content generation advisor. You need to suggest a trending topic to the researcher for blog generation after getting the company details from the admin. Research on what are things that are trending in the news regarding the domain."""
        )
        self.advisor.register_reply(
            [autogen.Agent, None],
            reply_func=self.print_messages,
            config={"callback": None},
        )

        self.researcher = autogen.AssistantAgent(
            name="researcher",
            llm_config=llm_config_assistant,
            max_consecutive_auto_reply=5,
            system_message="""You are a research expert, your job is to research on a topic given by the advisor and provide it as a research material to the writer."""
        )
        self.researcher.register_reply(
            [autogen.Agent, None],
            reply_func=self.print_messages,
            config={"callback": None},
        )

        self.writer = autogen.AssistantAgent(
            name="writer",
            llm_config=llm_config_writer,
            max_consecutive_auto_reply=5,
            system_message="""You are a blog writer. You would get a research material from the researcher. Use it to generate a nice blog on it, add TERMINATE to the end of the message."""
        )
        self.writer.register_reply(
            [autogen.Agent, None],
            reply_func=self.print_messages,
            config={"callback": None},
        )

        self.Admin = UserProxyWebAgent( 
            name="admin",
            human_input_mode="ALWAYS",
            max_consecutive_auto_reply=5, 
            system_message="""You are the admin of the blog generation team, after getting the company details, interact with the advisor to get a trending topic for blog generation. If the user suggests any topic no need to interact with advisor, directly interact with researcher.""",
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,
            function_map={"get_info_about": self.get_info_about},
            websocket=websocket
        )
        
        #self.Admin.register_reply(
        #    [autogen.Agent, None],
        #    reply_func=self.print_messages,
        #    config={"callback": None},
        #)

        # add the queues to communicate 
        # self.Admin.set_queues(self.client_sent_queue)

        self.groupchat = autogen.GroupChat(agents=[self.Admin, self.advisor, self.researcher, self.writer], messages=[], max_round=20)
        self.manager = GroupChatManagerWeb(groupchat=self.groupchat, 
            llm_config=llm_config_assistant,
            human_input_mode="ALWAYS" )

    async def print_messages(self, recipient, messages, sender, config):
        if "callback" in config and config["callback"] is not None:
            callback = config["callback"]
            callback(sender, recipient, messages[-1])
        message = messages[-1]["content"]
        response = {
            "author": recipient.name,
            "message": message
            }
        await self.websocket.send(json.dumps(response))
        return False, None     

    async def start(self):
        await self.Admin.a_initiate_chat(
            self.manager,
            clear_history=True,
            message="I am Pramit, CEO of Pushpa Furniture, We build home furniture with modern design and durability."
        )
    #MOCH Function call 
    #def search_db(self, order_number=None, customer_number=None):
    #    return "Order status: delivered TERMINATE"

    def get_info_about(self, topic):
        """
        Get the blog information
        """
        search = SearchApiAPIWrapper(searchapi_api_key = "54ee3pqqkfu7nSm4TcMLPqB1", engine="google")
        res = search.run("furniture trends")
        return res
