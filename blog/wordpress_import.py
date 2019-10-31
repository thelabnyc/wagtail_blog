from wordpress import API


class WordpressImport():
    def get_api(self, url: str, username: str, password: str):
        import ipdb; ipdb.set_trace()
        return API(
            url=url,
            api="wp-json",
            version='wp/v2',
            wp_user=username,
            wp_pass=password,
            basic_auth = True,
            user_auth = True,
        )


