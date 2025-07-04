class DorkLibrary:
    @staticmethod
    def high_risk_file_leaks(domain):
        return [
            f'site:{domain} ext:env OR ext:ini OR ext:config OR ext:bak',
            f'site:{domain} inurl:"index of /" "wp-config"',
            f'site:{domain} filetype:sql OR filetype:db',
            f'site:{domain} inurl:admin filetype:php',
            f'site:{domain} inurl:upload intext:confidential',
        ]

    @staticmethod
    def cms_targets(domain):
        return [
            f'site:{domain} inurl:/wp-content/uploads ext:xlsx',
            f'site:{domain} inurl:/wp-content/uploads ext:pdf "confidential"',
            f'site:{domain} intitle:"index of /wp-content/plugins"',
            f'site:{domain} inurl:/SiteAssets/forms/allitems.aspx',