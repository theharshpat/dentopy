from typing import Any, Optional, Dict, List, Type
import click
import json
import os

def process_file(file_path: str, output_directory: str):
    with open(file_path, 'r') as file:
        data = json.loads(file.read())

    if not isinstance(data, list):
        raise ValueError('Data is not a list')

    print(f'File contains {len(data)} items')

    pydantic_model_name = ''.join(part.capitalize() for part in file_path.split('/')[-1].split('.')[0].rstrip('s').split('_'))
    model_content = [f"class {pydantic_model_name}(BaseModel):"]

    fields: Dict[str, str] = {}
    keys_frequency: Dict[str, int] = {}
    for item in data:
        for key in item.keys():
            keys_frequency[key] = keys_frequency.get(key, 0) + 1

    for key in keys_frequency:
        all_values = [item.get(key) for item in data if key in item]
        field_type = "Any"  # Default type
        if all(isinstance(val, dict) for val in all_values if val is not None):
            field_type = "Dict[str, Any]"
        elif all(isinstance(val, list) for val in all_values if val is not None):
            list_type = "Any"  # Simplified to Any for mixed or empty lists
            if all_values and all_values[0]:
                list_types = set(type(val).__name__ for val in all_values[0] if val is not None)
                if len(list_types) == 1:
                    list_type = list(list_types)[0]
            field_type = f"List[{list_type}]"
        elif all(isinstance(val, str) for val in all_values if val is not None):
            field_type = "str"
        elif all(isinstance(val, int) for val in all_values if val is not None):
            field_type = "int"
        elif all(isinstance(val, float) for val in all_values if val is not None):
            field_type = "float"
        elif all(isinstance(val, bool) for val in all_values if val is not None):
            field_type = "bool"

        if keys_frequency[key] < len(data):  # Field is not present in all items, make it optional
            fields[key] = f"Optional[{field_type}] = None"
        else:
            fields[key] = field_type
        model_content.append(f"    {key}: {fields[key]}")

    model_definition = "\n".join(model_content)
    output_file_path = os.path.join(output_directory, f"{pydantic_model_name}.py")
    os.makedirs(output_directory, exist_ok=True)
    with open(output_file_path, 'w') as output_file:
        output_file.write(model_definition)
    print(f'Model {pydantic_model_name} written to {output_file_path}')

@click.command()
@click.option('--input-directory', default='input', type=click.Path(exists=True, file_okay=False), help='Directory containing input JSON files.')
@click.option('--output-directory', default='output', type=click.Path(file_okay=False), help='Directory where output models will be stored.')
def main(input_directory, output_directory):
    files = os.listdir(input_directory)
    print(f'Found {len(files)} files in the input directory: {input_directory}')
    for file_name in files:
        file_path = os.path.join(input_directory, file_name)
        if not file_path.endswith('.json'):
            print(f'Skipping a non-json file: {file_path}')
            continue
        print(f'Processing file: {file_path}')
        process_file(file_path, output_directory)
        print(f'File processed: {file_path}')
        print("\n\n")

if __name__ == '__main__':
    main()
