from log import logger


class RouterHelp:

    def list_routers(self, r, tab=0, s="\t"):
        for r in r.sub_routers:
            logger.info(f'{s*tab}{r}')
            # {r.observers}')
            # logger.info(f'{[v for k, v in r.observers.items()]}')
            if r.sub_routers:
                self.list_routers(r, tab+1)
