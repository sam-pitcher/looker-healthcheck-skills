view: users {
  sql_table_name: `project.analytics.users` ;;

  dimension: user_id {
    primary_key: yes
    type: number
    hidden: yes
    description: "Internal synthetic user identifier"
    sql: ${TABLE}.user_id ;;
  }

  dimension: country {
    type: string
    description: "Standard ISO country name of user residency"
    sql: ${TABLE}.country ;;
  }

  dimension: email {
    type: string
    description: "Verified customer contact email address"
    sql: ${TABLE}.email ;;
  }

  measure: count {
    type: count
    description: "Total count of registered customer profiles"
  }
}
