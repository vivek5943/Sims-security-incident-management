"""
FIX-04: Pre-download NLTK data during deployment setup.
Run once: python manage.py download_nltk_data
This replaces runtime auto-download which fails without internet in production.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Pre-download all NLTK corpora required by the ML NLP pipeline (run once during setup)'

    def handle(self, *args, **options):
        import nltk
        REQUIRED = [
            ('punkt',       'tokenizers/punkt'),
            ('punkt_tab',   'tokenizers/punkt_tab'),
            ('stopwords',   'corpora/stopwords'),
            ('wordnet',     'corpora/wordnet'),
            ('omw-1.4',     'corpora/omw-1.4'),
        ]
        self.stdout.write(self.style.MIGRATE_HEADING('\n  SIMS NLTK Data Downloader'))
        all_ok = True
        for name, check_path in REQUIRED:
            try:
                nltk.data.find(check_path)
                self.stdout.write(f'  ℹ  Already present: {name}')
            except LookupError:
                try:
                    nltk.download(name, quiet=True)
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Downloaded: {name}'))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'  ❌ Failed to download {name}: {e}'))
                    all_ok = False

        if all_ok:
            self.stdout.write(self.style.SUCCESS('\n  ✅ All NLTK data ready. ML pipeline can now run offline.\n'))
        else:
            self.stderr.write(self.style.ERROR('\n  ❌ Some downloads failed. Check internet connection.\n'))
