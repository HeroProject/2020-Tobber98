import argparse
import unirest
import random
import requests
import validators
import praw
import csv
import redis
import time
from threading import Thread

class api_methods:
    def __init__(self, server):
        # Keys for the various APIs
        self.last_fm_key = '7f822dc0e77dcd89dffb383a67d59c7b'
        self.imgur_key = '84ceaa883eb2b1f'
        self.eventbrite_key = 'BMPXJKQGLHLWFUDCFM3Q'
        self.flickr_key = 'a8ab5f74d14bab486529d3d0705d5ab2'
        self.moviedb_key = 'fd4faf94194a37311248bcf3040d6cdb'
        self.reddit = praw.Reddit(client_id='VtO-opHBxcv4iA',
                                  client_secret='M839PSOrTizQEOOzwPDmAbkU5Hc',
                                  user_agent='test1')

        # List of movie genres and their respective IDs
        self.movie_genres = [{'id': 28, 'name': 'action'}, {'id': 12, 'name': 'adventure'},
                             {'id': 16, 'name': 'animation'},
                             {'id': 35, 'name': 'comedy'}, {'id': 80, 'name': 'crime'},
                             {'id': 99, 'name': 'documentary'},
                             {'id': 18, 'name': 'drama'}, {'id': 10751, 'name': 'family'},
                             {'id': 14, 'name': 'fantasy'},
                             {'id': 36, 'name': 'history'}, {'id': 27, 'name': 'horror'},
                             {'id': 10402, 'name': 'music'},
                             {'id': 9648, 'name': 'mystery'}, {'id': 10749, 'name': 'romance'},
                             {'id': 878, 'name': 'science fiction'},
                             {'id': 878, 'name': 'sci-fi'}, {'id': 878, 'name': 'scifi'},
                             {'id': 10770, 'name': 'tv movie'},
                             {'id': 53, 'name': 'thriller'}, {'id': 10752, 'name': 'war'},
                             {'id': 37, 'name': 'western'}]

        # Pairs each subtopic to the function it needs to call within the api_methods class
        self.subtopic_API_pairs = {
            'music_artist': ['get_similar_artists'],
            'music_genre': ['get_genre_top_tracks'],
            'movie_actor': ['movie_call'],
            'movie_director': ['movie_call'],
            'movie_genre': ['movie_call'],
            'movie_fav_movie': ['movie_call'],
            'travel_has_visited': ['flickr_call'],
            'travel_wants_to_visit': ['flickr_call'],
            'sports_indiv_sport': ['flickr_call_sports'],
            'sports_team_sport': ['flickr_call_sports'],
        }

        # Initialise Redis
        self.redis = redis.Redis(host=server)
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe('action_webrequest')

    def update(self):
        msg = self.pubsub.get_message()
        if msg is not None:
            t = Thread(target=self.get_content, args=(msg['data'],))
            t.start()
        else:
            time.sleep(0)

    def produce(self, url, text):
        self.redis.publish('webrequest_response', url + '|' + text)

    # Main function that will be used in the Pepper program.
    # Queries the appropriate API, and parses the results such that it always returns an object with a 'text' and 'url' item.
    def determine_subtopic_query(self, data):
        global randomized
        if data == '':
            dict = {}
            with open('subtopic_querys.csv', mode='r') as infile:
                reader = csv.reader(infile, delimiter=',', quotechar='"', skipinitialspace=True)
                for row in reader:
                    try:
                        key = row[0]
                        val = row[1].strip()
                        if key in dict:
                            dict[key].append(val)
                        else:
                            dict[key] = [val]
                    except Exception:
                        continue
            subtopic = random.choice(list(self.subtopic_API_pairs))
            chosenList = dict[subtopic]
            query = random.choice(chosenList)
            randomized = True
        else:
            topic_object = data.split('|')
            subtopic = topic_object[0]
            query = topic_object[1]
            randomized = False
        return subtopic, query

    def get_content(self, data):
        subtopic, query = self.determine_subtopic_query(data)
        subtopic_method = self.subtopic_API_pairs.get(subtopic)[0]
        method_to_call = getattr(self, subtopic_method)
        if subtopic_method == 'movie_call':
            kwargs = {}
            if subtopic == 'movie_actor':
                kwargs['actor_query'] = query
            elif subtopic == 'movie_director':
                kwargs['director_query'] = query
            elif subtopic == 'movie_genre':
                kwargs['genre_query'] = query
            elif subtopic == 'movie_fav_movie':
                kwargs['movie_query'] = query
            results = method_to_call(**kwargs)
            for attr, val in results.iteritems():
                if len(val) > 0:
                    results = val
        else:
            results = method_to_call(query)
        try:
            result = random.choice(results)
        except Exception:
            result = results
        if type(result) == dict:
            result = result.values()
        elif type(result) != list:
            result = [result]

        print subtopic + " & " + query
        print result
        url = 'https://www.dictionary.com/e/wp-content/uploads/2018/08/disappointed-face.png'
        text = "Oops. I'm sorry, I can't find what I was planning to show you."
        for i in result:
            try:
                if validators.url(i) == True:
                    url = i
                else:
                    text = i
            except Exception:
                continue
        # return ([url, text])
        self.produce(url, text)

    def pick_top_track(self, artist):
        import xml.etree.ElementTree
        response = unirest.post('https://ws.audioscrobbler.com/2.0/',
                                params={
                                    'method': 'artist.gettoptracks',
                                    'lang': 'en',
                                    'artist': artist,
                                    'api_key': self.last_fm_key
                                }
                                )
        response = xml.etree.ElementTree.XML(response.body)
        top_tracks = []

        i = 0
        for track in response.findall('.//track'):
            if i < 10:
                current_track = track.find('name').text
                top_tracks.append(current_track)
        return top_tracks

    def get_genre_top_tracks(self, genre):
        genre_top_tracks = []
        params = {
            'method': 'tag.gettoptracks',
            'tag': genre,
            'limit': '30',
            'autocorrect': '1',
            'api_key': self.last_fm_key,
            'format': 'json'
        }
        response = requests.get('http://ws.audioscrobbler.com/2.0/', params=params)
        tracks = response.json().get('tracks').get('track')
        for track in tracks:
            artist_name = track.get('artist').get('name')
            track_name = track.get('name')
            if randomized == False:
                pepper_text = "Considering you're into " + genre + " music, you may like this song by " + artist_name + '. It is called ' + track_name + '.'
            else:
                pepper_text = 'You may like this song by ' + artist_name + '. It is called ' + track_name + '.'
            track_url = track.get('url')
            genre_top_tracks.append([pepper_text, track_url])
        return genre_top_tracks

    def get_similar_artists(self, artist_input):
        similar_artists = []
        params = {
            'method': 'artist.getsimilar',
            'artist': artist_input,
            'limit': '30',
            'autocorrect': '1',
            'api_key': self.last_fm_key,
            'format': 'json'
        }
        response = requests.get("http://ws.audioscrobbler.com/2.0/", params=params)
        try:
            artists = response.json().get('similarartists').get('artist')
        except Exception:
            artists = []
        for artist in artists:
            artist_name = artist.get('name')
            if randomized == False:
                text = 'Since you like ' + artist_input + ', I think you might also like ' + artist_name
            else:
                text = 'I think ' + artist_name + ' is really great. You should check it out!'
            artist_link = artist.get('url')
            similar_artists.append([text, artist_link])
        return similar_artists

    def flickr_call(self, search):
        params = {
            'api_key': self.flickr_key,
            'format': 'json',
            'nojsoncallback': '1',
            'extras': 'url-o',
            'tags': search + ', landscape, nature, -people, -person, -humans, -human',
            'tag_mode': 'all',
            'sort': 'relevance',
            'content_type': 1,
            'media': 'photo'
        }
        response = requests.get('https://api.flickr.com/services/rest/?method=flickr.photos.search', params=params)
        photos = response.json().get('photos').get('photo')
        photoList = []
        for photo in photos:
            farm = str(photo.get('farm'))
            server = str(photo.get('server'))
            id = str(photo.get('id'))
            secret = str(photo.get('secret'))
            url = 'https://farm' + farm + '.staticflickr.com/' + server + '/' + id + '_' + secret + '_b.jpg'
            title = photo.get('title')
            # text = 'This photo is titled: ' + title
            text = 'This photo was made in ' + search + ' and its title is: ' + title
            photoList.append([url, text])
        return photoList

    def flickr_call_sports(self, search):
        if search.lower() == 'football':
            search = 'soccer'
        params = {
            'api_key': self.flickr_key,
            'format': 'json',
            'nojsoncallback': '1',
            'extras': 'url-o',
            'tags': search,
            'tag_mode': 'all',
            'sort': 'interestingness-desc',
            'content_type': 1,
            'media': 'photo',
            'group_id': '83901175@N00'
        }
        response = requests.get('https://api.flickr.com/services/rest/?method=flickr.photos.search', params=params)
        photos = response.json().get('photos').get('photo')
        photoList = []
        for photo in photos:
            farm = str(photo.get('farm'))
            server = str(photo.get('server'))
            id = str(photo.get('id'))
            secret = str(photo.get('secret'))
            url = 'https://farm' + farm + '.staticflickr.com/' + server + '/' + id + '_' + secret + '_b.jpg'
            title = photo.get('title')
            # text = 'This photo is titled: ' + title
            if randomized == False:
                text = 'Since you enjoy ' + search + " , I think you may like this picture. It's called: " + title
            else:
                text = "Here's a picture related to " + search + ". It's called: " + title
            photoList.append([url, text])
        return photoList[:30]

    def parse_movie_results(self, input_response, query, query_topic):
        movie_list = []
        results = input_response.json().get('results')
        for result in results:
            movie_title = result.get('title')
            if query_topic == 'genre':
                movie_text = "Here's a cool " + query + " movie that you might enjoy. It's called: " + movie_title
            elif query_topic == 'actor':
                movie_text = "This is a cool movie starring " + query + ". It's called: " + movie_title
            elif query_topic == 'director':
                if randomized == False:
                    movie_text = "You should see " + movie_title + ". It's from your favorite director, " + query
                else:
                    movie_text = "I think you should go and see " + movie_title + " some time. It was directed by one of my personal favorite directors: " + query
            movie_backdrop = result.get('backdrop_path')
            if movie_backdrop == None:
                continue
            movie_backdrop = 'https://image.tmdb.org/t/p/w1280/' + str(movie_backdrop)
            movie_list.append([movie_backdrop, movie_text])
        return movie_list

    def get_person_ID(self, person):
        params = {
            'api_key': self.moviedb_key,
            'query': person
        }
        response = requests.get('https://api.themoviedb.org/3/search/person', params=params)
        results = response.json().get('results')
        try:
            person = results[0].get('id')
        except Exception:
            person = '999999999999'  # If we can't find the person, set person ID to a non-existent one. This makes the query return nothing
        return person

    def movie_call(self, movie_query=None, actor_query=None, director_query=None, genre_query=None):
        # https://developers.themoviedb.org/3/getting-started/introduction
        movie_recommendations = []
        actor_credit_list = []
        director_credit_list = []
        movie_genre_list = []
        actor_director_combined_list = []
        actor_genre_combined_list = []

        if movie_query != None:  # Get a list of recommended movies, based on input movie
            params = {
                'api_key': self.moviedb_key,
                'query': movie_query
            }
            response = requests.get('https://api.themoviedb.org/3/search/movie', params=params)
            movies = response.json().get('results')
            try:
                movie_ID = movies[0].get('id')
            except Exception:
                movie_ID = '999999999999'

            params2 = {
                'api_key': self.moviedb_key,
                'append_to_response': 'recommendations'
            }
            response = requests.get('https://api.themoviedb.org/3/movie/' + str(movie_ID), params=params2)
            try:
                recommendations = response.json().get('recommendations').get('results')
            except Exception:
                recommendations = []
            for recommendation in recommendations:
                title = recommendation.get('title')
                if randomized == False:
                    text = "You told me that you liked the movie: " + movie_query + ". You may also enjoy this one. It's called: " + title
                else:
                    text = "This is a movie I watched some time ago. It's called: " + title
                movie_backdrop = recommendation.get('backdrop_path')
                if movie_backdrop == None:
                    continue
                movie_backdrop = 'https://image.tmdb.org/t/p/w1280/' + str(movie_backdrop)
                movie_recommendations.append([movie_backdrop, text])
        if actor_query != None:  # Get input actor's most popular movies
            actor_ID = self.get_person_ID(actor_query)
            params = {
                'api_key': self.moviedb_key,
                'with_cast': actor_ID,
                'sort_by': 'vote_average.desc',
                'vote_count.gte': '200'
            }
            response = requests.get('https://api.themoviedb.org/3/discover/movie', params=params)
            actor_credit_list = self.parse_movie_results(response, actor_query, 'actor')
        if director_query != None:  # Get input director's most popular movies
            director_ID = self.get_person_ID(director_query)

            params = {
                'api_key': self.moviedb_key,
                'with_crew': director_ID,
                'sort_by': 'vote_average.desc',
                'vote_count.gte': '200'
            }
            response = requests.get('https://api.themoviedb.org/3/discover/movie', params=params)
            director_credit_list = self.parse_movie_results(response, director_query, 'director')
        if genre_query != None:  # Get highest rated movies of input genre
            for item in self.movie_genres:
                if item.get('name', None) == genre_query.lower():
                    genre_ID = item.get('id', None)
                    break
            if 'genre_ID' in locals():
                params = {
                    'api_key': self.moviedb_key,
                    'with_genres': genre_ID,
                    'sort_by': 'vote_average.desc',
                    'vote_count.gte': '200'
                }
                response = requests.get('https://api.themoviedb.org/3/discover/movie', params=params)
                movie_genre_list = self.parse_movie_results(response, genre_query, 'genre')
        return {'movie_recommendations': movie_recommendations, 'actor_popular': actor_credit_list,
                'director_popular': director_credit_list,
                'genre_recommendations': movie_genre_list}
               
               
    def runForever(self):
        try:
            while True:
                self.update()
        except KeyboardInterrupt:
            print 'Interrupted'
            self.pubsub.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=str, default='localhost', help='Server IP address. Default is localhost.')
    args = parser.parse_args()

    api_methods = api_methods(server=args.server)
    api_methods.runForever()