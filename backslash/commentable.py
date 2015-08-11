from .lazy_query import LazyQuery

class Commentable(object):

    def post_comment(self, comment):
        return self.client.api.call_function('post_comment', {
            'comment': comment,
            '{}_id'.format(self.type): self.id
            })

    def get_comments(self):
        return LazyQuery(self.client, '/rest/comments', query_params={'{}_id'.format(self.type): self.id})
