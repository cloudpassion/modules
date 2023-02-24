from ..http import Http


class DetailsExtra(Http):

    details_id: int

    async def get_showtab(self, key, parsed=True):
        resp = await self.get(
            url=f'https://{self.host}/get_srv_details.php'
                f'?id={self.details_id}'
                f'&pagesd={key}',
            headers={
                'referer': f'https://{self.host}/details.php?id={self.details_id}',
            }
        )
        return resp

    async def get_action(self, key, parsed=True):
        resp = await self.get(
            url=f'https://{self.host}/get_srv_details.php'
                f'?id={self.details_id}'
                f'&action={key}',
            headers={
                'referer': f'https://{self.host}/details.php?id={self.details_id}',
            }
        )
        return resp

