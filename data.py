import collections
import os
import json
#import pathlib

BlueArchiveData = collections.namedtuple(
    'BlueArchiveData',
    ['campaign_stages', 'campaign_stage_rewards', 'campaign_strategy_objects', 'campaign_units', 'characters',
     'currencies', 'equipment', 'event_content_stages', 'gacha_elements', 'gacha_elements_recursive', 'gacha_groups',
     'items', 'localization']
)
BlueArchiveTranslations = collections.namedtuple(
    'BlueArchiveTranslations',
    ['strategies']
)


def load_campaign_stages(path):
    return load_file(os.path.join(path, 'Excel', 'CampaignStageExcelTable.json'))


def load_campaign_stage_rewards(path):
    return load_file_grouped(os.path.join(path, 'Excel', 'CampaignStageRewardExcelTable.json'), 'GroupId')


def load_campaign_strategy_objects(path):
    return load_file(os.path.join(path, 'Excel', 'CampaignStrategyObjectExcelTable.json'))


def load_campaign_units(path):
    return load_file(os.path.join(path, 'Excel', 'CampaignUnitExcelTable.json'))


def load_characters(path):
    # TODO: find something better to use as the key
    return load_file(os.path.join(path, 'Excel', 'CharacterExcelTable.json'),
                     key='ModelPrefabName',
                     pred=lambda item: item['ProductionStep'] == 'Release')


def load_currencies(path):
    return load_file(os.path.join(path, 'Excel', 'CurrencyExcelTable.json'), key='ID')


def load_data(path_primary, path_secondary, path_translation):
    return BlueArchiveData(
        campaign_stages=load_campaign_stages(path_primary),
        campaign_stage_rewards=load_campaign_stage_rewards(path_primary),
        campaign_strategy_objects=load_campaign_strategy_objects(path_primary),
        campaign_units=load_campaign_units(path_primary),
        characters=load_characters(path_primary),
        currencies=load_currencies(path_primary),
        event_content_stages=load_event_content_stages(path_primary),
        gacha_elements=load_gacha_elements(path_primary),
        gacha_elements_recursive=load_gacha_elements_recursive(path_primary),
        gacha_groups=load_gacha_groups(path_primary),
        items=load_items(path_primary),
        equipment=load_equipment(path_primary),
        localization=load_localization(path_primary, path_secondary, path_translation),
    )


#def load_data(path):
#    return _load_data(pathlib.Path(path))


def load_equipment(path):
    return load_file(os.path.join(path, 'Excel', 'EquipmentExcelTable.json'))


def load_event_content_stages(path):
    return load_file(os.path.join(path, 'Excel', 'EventContentStageExcelTable.json'))


def load_file(file, key='Id', pred=None):
    with open(file,encoding="utf8") as f:
        data = json.load(f)
    return {item[key]: item for item in data['DataList'] if not pred or pred(item)}


def load_file_grouped(file, key="Id"):
    with open(file,encoding="utf8") as f:
        data = json.load(f)
    groups = collections.defaultdict(list)
    for item in data['DataList']:
        groups[item[key]].append(item)

    return dict(groups)


def load_gacha_elements(path):
    return load_file_grouped(os.path.join(path, 'Excel', 'GachaElementExcelTable.json'), 'GachaGroupID')


def load_gacha_elements_recursive(path):
    return load_file_grouped(os.path.join(path, 'Excel', 'GachaElementRecursiveExcelTable.json'), 'GachaGroupID')


def load_gacha_groups(path):
    return load_file(os.path.join(path, 'Excel', 'GachaGroupExcelTable.json'), key='ID')


def load_items(path):
    return load_file(os.path.join(path, 'Excel', 'ItemExcelTable.json'))


def load_strategies_translations(path):
    return load_file(os.path.join(path, 'Strategies.json'), key='Name')


#def load_translations(path):
#    return _load_translations(pathlib.Path(path))


def load_translations(path):
    return BlueArchiveTranslations(
        strategies=load_strategies_translations(path)
    )


def load_localization(path_primary, path_secondary, translation):
    data_primary = load_file(os.path.join(path_primary, 'Excel', 'LocalizeEtcExcelTable.json'), key='Key')
    data_secondary = load_file(os.path.join(path_secondary, 'Excel', 'LocalizeEtcExcelTable.json'), key='Key')
    data_aux = None

    index_list = list(data_primary.keys())
    index_list.extend(x for x in list(data_secondary.keys()) if x not in index_list)


    if os.path.exists(os.path.join(translation, 'LocalizeEtcExcelTable.json')):
        print(f'Loading additional translations from {translation}/LocalizeEtcExcelTable.json')
        data_aux = load_file(os.path.join(translation, 'LocalizeEtcExcelTable.json'))

        index_list.extend(x for x in list(data_aux.keys()) if x not in index_list)

    for index in index_list:
        try: 
            if data_aux != None and index in data_aux:
                data_primary[index] = data_aux[index] 
                #print(f'Loaded aux translation {index}')
            else :
                data_primary[index] = data_secondary[index] 
                #print(f'Loaded aux translation {index}')
            #print (f'FOUND secondary data for localize item {index}')
        except KeyError:
            #print (f'No secondary data for localize item {index}')
            continue
    
    return data_primary
