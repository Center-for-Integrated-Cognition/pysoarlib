from pysoarlib import SoarWME

def soar_identifier_to_json(soar_id):
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
            processed_value = soar_identifier_to_json(child_id)
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
