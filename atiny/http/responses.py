try:
    import responses
    @responses.activate
    def requests_simulate(url='http://ggg', code=200, text='simulate',
                          js={}, content_type='text/plain', proxy=None, path=None, tmp_dir=''):

        if js:
            responses.add(responses.GET, url,
                          json=js, status=code)
        else:
            responses.add(responses.GET, url,
                          body=text, status=code,
                          content_type=content_type)

        _resp = requests.get(url)

        return MergeResp(
            _resp.text, _resp.content, _resp.headers, _resp.status_code, _resp.url,
            path=tmp_dir+path if path \
                                 and isinstance(path, str) \
                else MyHttpUtils().make_path(url, tmp_dir=tmp_dir) if path else None,
            proxy=proxy, error=False
        )


except ImportError:
    pass
