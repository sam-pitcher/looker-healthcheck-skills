# Score 0 Anti-Pattern View: Missing primary key, casing issues, missing descriptions
view: bad_orders {
  sql_table_name: `project.analytics.orders` ;;

  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
  }

  dimension: user_id {
    type: number
    sql: ${TABLE}.user_id ;;
  }

  dimension: Order_Amount {
    type: number
    sql: ${TABLE}.amount ;;
  }

  measure: Total_Revenue {
    type: sum
    sql: ${TABLE}.amount ;;
  }
}
