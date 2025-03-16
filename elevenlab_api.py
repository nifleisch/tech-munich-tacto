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