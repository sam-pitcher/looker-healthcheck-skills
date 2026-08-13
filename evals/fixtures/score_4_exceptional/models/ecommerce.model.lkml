connection: "bigquery_ecommerce"

include: "/explores/*.explore.lkml"
include: "/views/*.view.lkml"
include: "/tests/*.test.lkml"

datagroup: etl_sync_datagroup {
  max_cache_age: "24 hours"
  sql_trigger: SELECT MAX(completed_at) FROM `project.etl.pipeline_runs` WHERE status = 'SUCCESS' ;;
}
