"""Management Command: train_ml_model — FIX-04, FIX-15"""
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Train SIMS Category + Severity ML classifiers and serialize to disk'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force retrain if models exist')

    def handle(self, *args, **options):
        from pathlib import Path
        from django.conf import settings

        cat_file = Path(settings.ML_MODEL_PATH) / 'sims_category_classifier.joblib'
        if cat_file.exists() and not options['force']:
            self.stdout.write(self.style.WARNING(
                '⚠  Models already trained. Use --force to retrain.\n'
                f'   Location: {settings.ML_MODEL_PATH}'
            ))
            return

        self.stdout.write(self.style.MIGRATE_HEADING('\n  SIMS ML Engine — Dual Classifier Training'))
        self.stdout.write('  FIX-15: Training Category (8 classes) + Severity (4 classes) models\n')
        try:
            from apps.ml_engine.trainer import train_and_save_model
            meta = train_and_save_model()
            self.stdout.write(self.style.SUCCESS(
                f'\n  ✅ Training complete!\n'
                f'     Category Model  : {meta["category_model"]} (F1={meta["category_f1"]})\n'
                f'     Severity Model  : {meta["severity_model"]} (F1={meta["severity_f1"]})\n'
                f'     Categories      : {", ".join(meta["categories"])}\n'
                f'     Severities      : {", ".join(meta["severities"])}\n'
                f'     Train Samples   : {meta["training_samples"]}\n'
                f'     TF-IDF Features : {meta["tfidf_features"]}\n'
                f'     ML Note         : {meta["note"]["CATEGORY"]}\n'
            ))
        except RuntimeError as e:
            self.stderr.write(self.style.ERROR(
                f'  ❌ Error: {e}\n'
                f'  Run python manage.py download_nltk_data first.\n'
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'  ❌ Training failed: {e}'))
            raise
