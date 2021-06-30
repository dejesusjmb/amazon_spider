import json
import argparse
import requests
from time import sleep


APIKEY = '551bff86e17c4582912d011ab4487c85'
PROJECT = '537486'


def run_spider(spider, asin):
    data = {
        'asin': asin,
        'spider': spider,
        'apikey': APIKEY,
        'project': PROJECT
    }
    response = requests.post(url='https://app.scrapinghub.com/api/run.json', data=data)
    return response.json()['jobid']


def get_spider_status(jobid):
    params = {
        'job': jobid,
        'apikey': APIKEY,
        'project': PROJECT
    }
    response = requests.get(url='https://app.scrapinghub.com/api/jobs/list.json', params=params)
    return response.json()['jobs'][0]['state']


def get_items(jobid):
    params = {'apikey': APIKEY, 'format': 'json'}
    response = requests.get(url=f'https://storage.scrapinghub.com/items/{jobid}', params=params)
    return response.json()


def scrape(args):
    print('Running spider')
    jobid = run_spider(args.spider, args.asin)
    items = []
    spider_status = None

    for _ in range(20):
        spider_status = get_spider_status(jobid)
        if spider_status == 'finished':
            print(f'Job {jobid} is finished! Fetching scraped items')
            items = get_items(jobid)
            print(f'Successfully fetched scraped items')
            break

        print(f'Job {jobid} is not yet finished. Waiting...')
        sleep(10)

    return items, spider_status


def save(asin, items):
    with open(f'{asin}.json', 'w') as f:
        f.write(json.dumps(items, indent=4))


def parse_arguments():
    parser = argparse.ArgumentParser(description='Scrape items from Amazon')
    parser.add_argument('--asin',
                        help='an integer for the accumulator')
    parser.add_argument('--spider',
                        help='spider name. amazon_uk or amazon_us')
    return parser.parse_args()


def main():
    args = parse_arguments()
    items, spider_status = scrape(args)
    if not items:
        raise Exception(f'No items scraped! Spider status: {spider_status}')
    else:
        save(args.asin, items)
        print(f'Successfully saved scraped items to {args.asin}.json')


if __name__ == "__main__":
    main()
