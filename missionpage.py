import collections
import io
import pathlib
import re
import sys
import os
import traceback
import argparse

from jinja2 import Environment, FileSystemLoader
from pywikiapi import Site

from data import load_data, load_translations
from mapper import load_assets, map_campaign_stage
from rewards import get_rewards

WIKI_API = 'https://bluearchive.wiki/w/api.php'
site = Site(WIKI_API)

CAMPAIGN_STAGE_NAME_PATTERN = r'^CHAPTER0*(?P<chapter>\d+)_(?P<difficulty>Hard|Normal)_Main_Stage0*(?P<stage>\d+)$'

BLOCK_START_STRING = "[%"
BLOCK_END_STRING = "%]"
VARIABLE_START_STRING = "[["
VARIABLE_END_STRING = "]]"
COMMENT_START_STRING = "[#"
COMMENT_END_STRING = "#]"

Mission = collections.namedtuple('Mission', 'name,cost,difficulty,environment,reclevel,filename,rewards,strategy')

args = None


#def formaticon(value):
#    return value.rsplit('/', 1)[-1] + '.png'


def get_campaign_stage(name, data):
    for campaign_stage in data.campaign_stages.values():
        try:
            campaign_stage_name = get_campaign_stage_name(campaign_stage)
        except ValueError:
            continue

        if campaign_stage_name == name:
            return campaign_stage

    raise KeyError


def get_campaign_stage_name(campaign_stage):
    chapter, stage, difficulty = parse_campaign_stage_name(campaign_stage['Name'])
    return f'{chapter}-{stage}{"H" if difficulty == "Hard" else ""}'


def parse_campaign_stage_name(name):
    m = re.match(CAMPAIGN_STAGE_NAME_PATTERN, name)
    if not m:
        raise ValueError

    return int(m.group('chapter')), int(m.group('stage')), m.group('difficulty')


def render_mission_page(name, campaign_stage, data, tls):
    environment_names = {
        'Street': 'Urban',
        'Indoor': 'Indoors',
        'Outdoor': 'Outdoors'
    }

    env = Environment(
        loader=FileSystemLoader(pathlib.Path(__file__).parent),
        block_start_string=BLOCK_START_STRING,
        block_end_string=BLOCK_END_STRING,
        variable_start_string=VARIABLE_START_STRING,
        variable_end_string=VARIABLE_END_STRING,
        comment_start_string=COMMENT_START_STRING,
        comment_end_string=COMMENT_END_STRING
    )
    #env.filters['formaticon'] = formaticon
    template = env.get_template('template.txt')
    mission = Mission(
        name,
        campaign_stage['StageEnterCostAmount'],
        parse_campaign_stage_name(campaign_stage['Name'])[2],
        environment_names[campaign_stage['StageTopography']],
        campaign_stage['RecommandLevel'],
        f'{campaign_stage["Name"]}.png',
        get_rewards(campaign_stage, data),
        tls.strategies[name]['Description']
    )
    return template.render(mission=mission)


def missionpage(map, data, tls, assets):
    global args, site

    campaign_stage = get_campaign_stage(map, data)

    text = render_mission_page(map, campaign_stage, data, tls)

    path = map + '_' + campaign_stage["Name"]

    with open(os.path.join(args['outdir'], f'{path}.txt'), 'w', encoding="utf8") as f:
        f.write(text)

    if args['wiki'] != None:  

        # Upload map image
        
        # with io.BytesIO() as b:
        #     map_campaign_stage(args['data_primary'], b, campaign_stage, data, assets)
        #     b.seek(0)
        #     site(
        #         action='upload',
        #         filename=f'{campaign_stage["Name"]}.png',
        #         comment=f'Upload map image for {map}',
        #         ignorewarnings=True,
        #         token=site.token(),
        #         POST=True,
        #         EXTRAS={
        #             'files': {
        #                 'file': b
        #             }
        #         }
        #     )

        # Upload mission page

        site(
            action='edit',
            title=f'Missions/{map}',
            text=text,
            summary=f'Generated mission page for {map}',
            token=site.token()
        )


def main():
    global args, site

    parser = argparse.ArgumentParser()

    parser.add_argument('map_id', metavar='MISSION NUMBER', help='Id of a single mission page or a comma-separated list to export')
    parser.add_argument('-data_primary', metavar='DIR', help='Fullest (JP) game version data')
    parser.add_argument('-data_secondary', metavar='DIR', help='Secondary (Global) version data to include localisation from')
    parser.add_argument('-translation', metavar='DIR', help='Additional translations directory')
    parser.add_argument('-outdir', metavar='DIR', help='Output directory')
    parser.add_argument('-wiki', nargs=2, metavar=('LOGIN', 'PASSWORD'), help='Publish data to wiki')
    #parser.add_argument('-wikipath', metavar='PATH', help='Parent material for the generated pages')

    args = vars(parser.parse_args())
    args['data_primary'] = args['data_primary'] == None and '../ba-data/jp' or args['data_primary']
    args['data_secondary'] = args['data_secondary'] == None and '../ba-data/global' or args['data_secondary']
    args['translation'] = args['translation'] == None and '../bluearchivewiki/translation' or args['translation']
    args['outdir'] = args['outdir'] == None and 'out' or args['outdir']
    #args['wikipath'] = args['wikipath'] == None and 'Missions' or args['wikipath']
    #print(args)
    try:
        data = load_data(args['data_primary'], args['data_secondary'], args['translation'])
        tls = load_translations(args['translation'])
        assets = load_assets()

        if args['wiki'] != None:  
            try:
                site = Site(WIKI_API)
                site.login(args['wiki'][0], args['wiki'][1])

                print(f'Logged in to wiki, token {site.token()}')
            except Exception as err:
                print(f'Wiki error: {err}')
                traceback.print_exc()


        for map in args['map_id'].split(','):
            missionpage(map, data, tls, assets)
    except:
        parser.print_help()
        traceback.print_exc()


if __name__ == '__main__':
    main()
