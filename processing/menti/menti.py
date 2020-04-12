#!/usr/bin/env python3

import argparse
import requests
import redis

BASE_URL = "https://www.menti.com"

def get_questions(self, code): # prints the questions for the given question code
    session = requests.session()
    session.get(BASE_URL)
    response = session.get(f"{BASE_URL}/core/objects/vote_ids/{code}")

    if response.status_code != 200:
        print("Invalid code")
        return
    else:
        response = response.json()
        for question in response["questions"]:
            redis.publish('action_menti_get_questions', f"""{question["question"]}""")



def get_results_url(self):  # prints the URL for the given question code
    session = requests.session()
    session.get(BASE_URL)
    response = session.get(f"{BASE_URL}/core/objects/vote_ids/{code}")

    if response.status_code != 200:
        print("Invalid code")
        return
    else:
        redis.publish('action_menti_get_results_url', f"""https://www.mentimeter.com/s/{response["series_id"]}/{response["questions"][0]["admin_key"]}""")


##### not used, but can be for voting if desired
def vote(self, question, answer, times):
    for i in range(times):
        session = requests.session()
        session.get(BASE_URL)
        response = session.post(f"{BASE_URL}/core/identifier")

        if response.status_code != 200:
            print("Failed to retrieve identifier")
            return
        else:
            response = response.json()
            identifier = response["identifier"]
            headers = {"x-identifier": identifier}
            payload = {"question": question, "question_type": "choices", "vote": answer}
            response = session.post(f"{BASE_URL}/core/vote", headers=headers, data=payload)
            status = "OK"

            if response.status_code != 200:
                status = "Error"
            
            print(f"Voting {i + 1}/{times}... {status}")
#####


def main(args, server):
    client = redis.Redis(host=server)
    pubsub = client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('action_menti')


    if args.code is not None and args.results is not None:  # get the results if the question code and the results flag are both used
        get_results_url():
    elif args.code is not None: # only get the question if only the question code is present
        get_questions(args.code)
    
    ##### can be used for voting
    # if args.question is not None and args.answer is not None:
    #     vote(args.question, args.answer, args.times)

    pubsub.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--code", type=int, help="get questions for code")
    parser.add_argument("-r", "--results", help="get results URL", action="store_true")
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    # parser.add_argument("-q", "--question", type=str, help="id for question")
    # parser.add_argument("-a", "--answer", type=str, help="id for answer")
    # parser.add_argument("-t", "--times", type=int, help="number of times to vote for answer", default=1)

    args = parser.parse_args()

    main(args, args.server)