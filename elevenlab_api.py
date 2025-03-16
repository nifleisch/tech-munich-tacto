import requests

from elevenlabs import ElevenLabs
agent_id = "7ZNPyYITxhYm97d1kY0q"


def delete_knowledge_base(client,key,agent_id = "7ZNPyYITxhYm97d1kY0q"):
    headers = {
        'xi-api-key': key,
    }
    response = requests.get('https://api.elevenlabs.io/v1/convai/knowledge-base', headers=headers)
    for dic in response.json()['documents']:
        id = dic['id']
        remove_knowledge_base_from_agent(client,agent_id = agent_id)
        response = requests.delete(f'https://api.elevenlabs.io/v1/convai/knowledge-base/{id}', headers=headers)
        print("Knowledge base deleted")

def update_agent(key,agent_id="7ZNPyYITxhYm97d1kY0q"):
    url =f"https://api.elevenlabs.io/v1/convai/agents/{id}"
    payload = {}
    headers = {
        "xi-api-key":key,
        "Content-Type": "application/json"
    }
    response = requests.patch(url, json=payload, headers=headers)
    print("Knowledge base updated")
    
def upload_context_file(key,file_path):
    headers = {
        'xi-api-key': key,
    }
    files = {
        'file': (file_path, open(file_path, 'rb'), 'text/plain'),
        'name': (None, ''),
    }
    response = requests.post('https://api.elevenlabs.io/v1/convai/knowledge-base', headers=headers, files=files)
    
    print("Context file uploaded")
    return response.json()['id']

def link_knowledge_base_to_agent(client,agent_id = "7ZNPyYITxhYm97d1kY0q",document_id = "jZCNew80TpRKjr6K6sPZ"):
  #client = ElevenLabs(api_key=key)        
  client.conversational_ai.update_agent(
    agent_id=agent_id,
      conversation_config={"agent":{"prompt":{"knowledge_base": [
            {
              "type": "file",
              "name": "history.txt",
              "id": document_id,
              "usage_mode": "auto"
            }
          ],}}})
def remove_knowledge_base_from_agent(client,agent_id = "7ZNPyYITxhYm97d1kY0q"):
    client.conversational_ai.update_agent(
    agent_id=agent_id,
      conversation_config={"agent":{"prompt":{"knowledge_base": [
            
          ],}}})
def upload_context(path,key,agent_id = "7ZNPyYITxhYm97d1kY0q"):
    client = ElevenLabs(api_key=key)
    delete_knowledge_base(client,key,agent_id=agent_id)
    update_agent(key,agent_id=agent_id)
    context_id = upload_context_file(key,path)
    link_knowledge_base_to_agent(client,document_id=context_id,agent_id=agent_id)



from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
key = "sk_1f973a4171012be7f5f13d7b0bd76d359f11d42d13b4c49e"
def call(key,agent_id= "7ZNPyYITxhYm97d1kY0q"):
  

  client = ElevenLabs(api_key=key)

  dynamic_vars = {
    "Suppliers_Name": "Angelo",
  }



  conversation = Conversation(
    client,
    agent_id,
    # Assume auth is required when API_KEY is set.
    requires_auth=bool(key),
    # Use the default audio interface.
    audio_interface=DefaultAudioInterface(),
    # Simple callbacks that print the conversation to the console.
    callback_agent_response=lambda response: print(f"Agent: {response}"),
    callback_agent_response_correction=lambda original, corrected: print(f"Agent: {original} -> {corrected}"),
    callback_user_transcript=lambda transcript: print(f"User: {transcript}"),
    # Uncomment the below if you want to see latency measurements.
    # callback_latency_measurement=lambda latency: print(f"Latency: {latency}ms"),
  )

  conversation.start_session()

  #signal.signal(signal.SIGINT, lambda sig, frame: conversation.end_session())


