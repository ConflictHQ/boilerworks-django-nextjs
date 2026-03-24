from core.tests.utils.base_test import BaseTest


class TestInternationalization(BaseTest):
    def test_get_site_labels(self):
        """
        # Get site labels
        Returns all the site labels for the default system language.
        :return:
        """
        request = self.request()

        query = '''
            query siteLabels($key: String, $locale:String) {
              siteLabels(key:$key, locale:$locale) {
                totalCount
                edges {
                  node {
                    key
                    text

                  }
                }
              }
            }
        '''
        variables = {'key': None, 'locale': None}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)

    def test_get_site_labels_filter_by_prefix(self):
        """
        # Get site labels by key (or prefix)
        Returns all the site labels that match the given key as a prefix.
        i.e. for the key about_page, you will get both about_page.title and about_page.description
        """
        request = self.request()

        query = '''
            query siteLabels($key: String, $locale:String) {
              siteLabels(key:$key, locale:$locale) {
                totalCount
                edges {
                  node {
                    key
                    text

                  }
                }
              }
            }
        '''
        variables = {'key': "company_info.management", 'locale': None}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)

    def test_get_site_labels_filter_by_locale(self):
        """
        # Get site labels for a specific locale
        Returns all the site labels for a specific system language.
        """
        request = self.request()

        query = '''
            query siteLabels($key: String, $locale:String) {
              siteLabels(key:$key, locale:$locale) {
                totalCount
                edges {
                  node {
                    key
                    text

                  }
                }
              }
            }
        '''
        variables = {'key': None, 'locale': "es"}
        response = self.client.execute(query, variables=variables, context_value=request)
        self.assertQueryResult(query, variables, response)
