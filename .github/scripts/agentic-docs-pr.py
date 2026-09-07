import requests
import json
import yaml

def get_structure(obj):
    if isinstance(obj, dict):
        return {k: get_structure(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        if obj:
            return [get_structure(obj[0])]
        return []
    else:
        return None

def get_value_by_path(data, path):
    keys = path.split('.')
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data

with open("MlogDocs/Languages/v8/en.yaml", "r") as f:
    en_yaml = yaml.safe_load(f)
    en_structure = get_structure(en_yaml)

with open('TRANSLATING.md', 'r') as f:
    translating_content = f.read()

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_value_by_path",
            "description": "Get a value from the YAML structure by its path",
            "parameters": {
            "type": "object",
            "properties": {
                "path": {
                "type": "string",
                "description": "Path to the desired value in the YAML structure, using dot notation for nested keys."
                }
            },
            "required": ["path"]
            }
        }
    }
]

test_changes = "2026-07-13 New logic rule musicVolume."

content = f"""
Documentation assistant, Updates the documentation based on the following changes: {test_changes}. 
Create a YAML response that uses dot notation with existing or new path to modify the value, if its an existing path include the original value with your changes, if its a new path include the new value. The value should be a description of the changes. 
If the information from the change is not sufficient, mark the value with "TODO" and provide a brief description of what is missing.
The YAML structure is as follows: {en_structure}
And the existing documentation is as follows: {translating_content}
If context of the existing documentation is needed, you can use the tool "get_value_by_path" to retrieve the existing value by its path in dot notation.
Respond only with either the YAML response or the tool call, and do not include any additional text or explanations.
"""

messages = [
    {"role": "user", "content": content}
]
session = []

session += messages

def generic_request(messages, tools):
    result = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer <OPENROUTER_API_KEY>",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
            "messages": messages,
            "reasoning": {"enabled": True},
            "tools": tools,
        })
    )
    return result

# Extract the assistant message with reasoning_details
response = generic_request(messages, tools)
response = response.json()
response = response['choices'][0]['message']

tool_response = []

if 'reasoning_details' in response:
    reasoning_details = response['reasoning_details']
if response.get('tool_calls') and not response.get('content'):
    is_tool_call = True
    while 'tool_calls' in response and response['tool_calls']:
        for tool_call in response['tool_calls']:
            if tool_call['name'] == 'get_value_by_path':
                path = tool_call['arguments']['path']
                # Call the get_value_by_path function to retrieve the existing value
                existing_value = get_value_by_path(en_yaml, path)
                print(f"Existing value at path '{path}': {existing_value}")
                tool_response.append({
                    "role": "tool",
                    "tool_call_id": tool_call['tool_call_id'],
                    "content": existing_value
                })

        session += tool_response

        response = generic_request(session, tools)
        response = response.json()
        response = response['choices'][0]['message']


yaml_response = response.get("content", "")

updates = yaml.safe_load(yaml_response)

for path, value in updates.items():
    current = en_yaml
    keys = path.split(".")

    for key in keys[:-1]:
        current = current.setdefault(key, {})

    current[keys[-1]] = value

with open("MlogDocs/Languages/v8/en.yaml", "w") as f:
    yaml.dump(en_yaml, f, default_flow_style=False, allow_unicode=True)








