from apps.core.models import Artist


def convert_tuples_to_dicts(tuples, field_names=None):
    if field_names is None:
        field_names = [field.name for field in Artist._meta.fields]
    result_list = []
    if isinstance(tuples, tuple):
        tuples = [tuples]
    for artist in tuples:
        result_dict = dict(zip(field_names, artist))
        result_list.append(result_dict)

    return result_list
