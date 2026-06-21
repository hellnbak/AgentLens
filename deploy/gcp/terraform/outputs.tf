output "artifact_registry" { value = google_artifact_registry_repository.repo.name }
output "archive_bucket" { value = google_storage_bucket.archive.name }
output "runtime_service_account" { value = google_service_account.runtime.email }
