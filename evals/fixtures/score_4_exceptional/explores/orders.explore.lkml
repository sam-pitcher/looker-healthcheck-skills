explore: orders {
  label: "Orders & Fulfillment Analysis"
  description: "Core sales and customer transaction explore accelerated with aggregate awareness"
  persist_with: etl_sync_datagroup

  join: users {
    type: left_outer
    relationship: many_to_one
    sql_on: ${orders.user_id} = ${users.user_id} ;;
  }

  aggregate_table: monthly_sales_summary {
    query: {
      dimensions: [orders.created_month, users.country]
      measures: [orders.total_revenue, orders.count]
      timezone: "UTC"
    }
    materialization: {
      datagroup_trigger: etl_sync_datagroup
    }
  }
}
