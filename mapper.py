import json
import pathlib
import sys
import traceback
import argparse

from PIL import Image

from data import load_data
from maputil import get_tiles
from tilemap import TileMap

args = None

def load_assets():
    return {asset: im for asset, im in _load_assets()}


def _load_assets():
    for asset in pathlib.Path().glob('assets/*.png'):
        yield asset.stem, Image.open(asset)


def create_tilemap(map, data):
    tilemap = TileMap()
    for location, tile in get_tiles(map, data):
        tilemap.set_cube(*location, tile)

    return tilemap


def render_tilemap(tilemap, assets):
    min_q, min_r, max_q, max_r = tilemap.bounds
    width = (max_q - min_q + 1) * 105 + 52
    height = (max_r - min_r + 2) * 80
    im = Image.new('RGBA', (width, height))
    tilemap.draw(im, assets, 105, 80, 52)
    return im


def map_campaign_stage(datadir, fp, campaign_stage, data, assets):
    strategy_map = campaign_stage['StrategyMap']
    if strategy_map is None:
        raise ValueError(f'Campaign stage {campaign_stage["Name"]} has no StrategyMap')

    try:
        map = json.loads(pathlib.Path(datadir, 'HexaMap', f'{strategy_map.lower()}.json').read_bytes())
    except FileNotFoundError:
        raise ValueError(f'HexaMap for campaign stage {campaign_stage["Name"]} does not exist')

    tilemap = create_tilemap(map, data)
    im = render_tilemap(tilemap, assets)
    im = im.crop(im.getbbox())
    im.save(fp, format='PNG')


def map_campaign_stages(datadir, outdir, data, assets):
    for campaign_stage in data.campaign_stages.values():
        outfile = pathlib.Path(outdir, campaign_stage['Name'] + '.png')
        try:
            map_campaign_stage(datadir, outfile, campaign_stage, data, assets)
        except ValueError as err:
            print(err)
            continue


def map_event_content_stage(datadir, fp, event_content_stage, data, assets):
    strategy_map = event_content_stage['StrategyMap']
    if strategy_map is None or strategy_map == 'StrategyMap_1011101':
        raise ValueError(f'Event content stage {event_content_stage["Name"]} has no StrategyMap')

    try:
        map = json.loads(pathlib.Path(datadir, 'HexaMap', f'{strategy_map.lower()}.json').read_bytes())
    except FileNotFoundError:
        raise ValueError(f'HexaMap for event content stage {event_content_stage["Name"]} does not exist')

    tilemap = create_tilemap(map, data)
    im = render_tilemap(tilemap, assets)
    im = im.crop(im.getbbox())
    im.save(fp, format='PNG')


def map_event_content_stages(datadir, outdir, data, assets):
    for event_content_stage in data.event_content_stages.values():
        outfile = pathlib.Path(outdir, event_content_stage['Name'] + '.png')
        try:
            map_event_content_stage(datadir, outfile, event_content_stage, data, assets)
        except ValueError as err:
            print(err)
            continue


def mapper(what):
    global args

    data = load_data(args['data_primary'], args['data_secondary'], args['translation'])
    assets = load_assets()
    if what == 'campaign':
        map_campaign_stages(args['data_primary'], args['outdir'], data, assets)
    elif what == 'events':
        map_event_content_stages(args['data_primary'], args['outdir'], data, assets)
    else:
        print(f"Don't know how to map {what}")


def main():
    global args

    parser = argparse.ArgumentParser()

    parser.add_argument('map_type', metavar='<campaign/events>', help='campaign/events')
    parser.add_argument('-data_primary', metavar='DIR', help='Fullest (JP) game version data')
    parser.add_argument('-data_secondary', metavar='DIR', help='Secondary (Global) version data to include localisation from')
    parser.add_argument('-translation', metavar='DIR', help='Additional translations directory')
    parser.add_argument('-outdir', metavar='DIR', help='Output directory')

    args = vars(parser.parse_args())
    args['data_primary'] = args['data_primary'] == None and '../ba-data/jp' or args['data_primary']
    args['data_secondary'] = args['data_secondary'] == None and '../ba-data/global' or args['data_secondary']
    args['translation'] = args['translation'] == None and '../bluearchivewiki/translation' or args['translation']
    args['outdir'] = args['outdir'] == None and 'out' or args['outdir']
    #print(args)
    try:
         mapper(args['map_type'])
    except:
        parser.print_help()
        traceback.print_exc()

if __name__ == '__main__':
    main()
