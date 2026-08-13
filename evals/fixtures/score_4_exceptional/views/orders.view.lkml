view: orders {
  sql_table_name: `project.analytics.orders` ;;

  dimension: order_id {
    primary_key: yes
    type: number
    description: "Unique synthetic transaction identifier"
    sql: ${TABLE}.order_id ;;
  }

  dimension: user_id {
    type: number
    hidden: yes
    description: "Foreign key reference to users table"
    sql: ${TABLE}.user_id ;;
  }

  dimension_group: created {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: ${TABLE}.created_at ;;
  }

  dimension: order_amount {
    type: number
    description: "Gross transaction currency amount in USD"
    sql: ${TABLE}.amount ;;
  }

  measure: count {
    type: count
    description: "Total count of distinct completed orders"
    drill_fields: [order_id, user_id, order_amount]
  }

  measure: total_revenue {
    type: sum
    description: "Total gross aggregated order revenue in USD"
    sql: ${order_amount} ;;
    drill_fields: [order_id, created_date, order_amount]
  }
}
