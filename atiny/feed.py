from collections import namedtuple
from feedgen.feed import FeedGenerator


class MyRfeed:
    def __init__(self):
        pass

    def create_item(self, title='', link='', description='', date='', author='feed'):

        rss_item = namedtuple(
            'rss_item',
            ('title', 'id', 'link', 'date')
        )
        return rss_item._make([
            title, link, link, date
        ])
        """
                item = rItem(
            title=title,
            link=link,
            description=description,
            author=author,
            guid=rGuid(link),
            pubDate=date
        )
        """

    def make_feed(self, title, description, link, items):
        fg = FeedGenerator()
        fg.title(title)
        fg.description(description)
        fg.link(href=link, rel="alternate", type="text/html")

        for item in items:
            fe = fg.add_entry()
            fe.id(item.link)
            fe.title(item.title)
            if link:
                fe.link(href=item.link, rel="alternate", type="text/html")
            fe.pubDate(item.date)

        #feed = rFeed(
        #    title=title,
        #    description=desription,
        #    link=link,
        #    items=items
       # )
        feed = fg.rss_str(pretty=True)
        return feed
