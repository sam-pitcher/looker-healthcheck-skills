# Score 0 Anti-Pattern View: Unhidden technical hash and missing primary key
view: bad_users {
  sql_table_name: `project.analytics.users` ;;

  dimension: id {
    type: number
    sql: ${TABLE}.id ;;
  }

  dimension: password_hash {
    type: string
    sql: ${TABLE}.password_hash ;;
  }

  dimension: email {
    type: string
    sql: ${TABLE}.email ;;
  }
}
