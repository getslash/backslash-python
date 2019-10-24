from .lazy_query import LazyQuery


class Commentable():

    def post_comment(self, comment):
        return self.client.api.call_function('post_comment', {
            'comment': comment,
            f'{self.type}_id': self.id
            })

    def get_comments(self):
        return LazyQuery(self.client, '/rest/comments', query_params={f'{self.type}_id': self.id})
