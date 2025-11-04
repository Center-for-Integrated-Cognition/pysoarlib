from pysoarlib import SoarWME

def add_json_to_soar_identifier(parent_id, json_object):
    print(json_object)
    print("Type:")
    print(type(json_object))
    node_wmes = {}

    if isinstance(json_object, dict):
        for key, value in json_object.items():
            add_json_to_soar_attribute(parent_id, key, value, node_wmes)
    # elif isinstance(json_object, list):
    #     new_id = parent_id.CreateIdWME("weird")
    #     for item in json_object:
    #         self.add_json_to_soar_attribute(new_id, 'item', item)
    else:
        print("Error root JSONmust be a dict")
        raise ValueError("The root JSON object must be a dictionary")

def add_json_to_soar_attribute(parent_id, attribute, json_object, node_wmes):
    if isinstance(json_object, dict):
        new_id = parent_id.CreateIdWME(attribute)
        for key, value in json_object.items():
            add_json_to_soar_attribute(new_id, key, value, node_wmes)
    elif isinstance(json_object, list):
        attr = attribute.rstrip("s") #plural set
        #new_id = parent_id.CreateIdWME(attribute)
        for item in json_object:
            add_json_to_soar_attribute(parent_id, attr, item, node_wmes)
    elif isinstance(json_object, bool):
        # Convert booleans to strings 'true' or 'false'
        parent_id.CreateStringWME(attribute, str(json_object).lower())
    elif isinstance(json_object, int):
        parent_id.CreateIntWME(attribute, json_object)
    elif isinstance(json_object, float):
        parent_id.CreateFloatWME(attribute, json_object)
    elif isinstance(json_object, str):
        if attribute == "node":
            node_wmes[json_object] = parent_id
        if "argument" in attribute and "node" in json_object:
            if node_wmes[json_object]:
                parent_id.CreateSharedIdWME(attribute, node_wmes[json_object])
            else:
                print("Error refered to node not found:" + json_object)
        else:
            parent_id.CreateStringWME(attribute, json_object)
