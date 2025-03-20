def convert_tuples_to_dicts(tuples, field_names=None):
    if field_names is None:
        raise Exception("Please provide field_names")
    result_list = []
    if isinstance(tuples, tuple):
        tuples = [tuples]
    for artist in tuples:
        result_dict = dict(zip(field_names, artist))
        result_list.append(result_dict)

    return result_list
