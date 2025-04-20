from your_app.models import KernelVersion, CVEState
from kernel_analysis.cve_analysis import evaluate_cve_applicability

def evaluate_all_cves(kernel_version_str: str, config_path: str):
    try:
        kernel_version = KernelVersion.objects.get(version=kernel_version_str)
    except KernelVersion.DoesNotExist:
        print(f"[❌] Kernel version {kernel_version_str} not found in DB.")
        return

    all_cves = CVEState.objects.all()

    for cve in all_cves:
        try:
            evaluate_cve_applicability(cve, kernel_version, config_path)
            print(f"[✔] {cve.cve_id} → {'Applicable' if cve.applicable else 'Not applicable'}")
        except Exception as e:
            print(f"[⚠️] Failed to evaluate {cve.cve_id}: {e}")
