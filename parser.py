# kernel_analysis/parser.py
... (existing content remains unchanged)

# kernel_analysis/management/commands/evaluate_cves.py
from django.core.management.base import BaseCommand
from kernel_analysis.cve_analysis import evaluate_all_cves

class Command(BaseCommand):
    help = "Evaluate all CVEs against a given kernel version and .config"

    def add_arguments(self, parser):
        parser.add_argument("version", type=str, help="Kernel version (e.g., 4.14.206)")
        parser.add_argument("config", type=str, help="Path to .config file")

    def handle(self, *args, **options):
        version = options["version"]
        config = options["config"]

        self.stdout.write(self.style.WARNING(f"🔍 Evaluating CVEs against kernel {version}..."))
        evaluate_all_cves(version, config)
        self.stdout.write(self.style.SUCCESS("✅ Done evaluating all CVEs."))
