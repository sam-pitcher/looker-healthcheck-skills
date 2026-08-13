# Score 0 Anti-Pattern Model: Monolithic, arbitrary caching, missing relationships
connection: "production_db"

explore: orders {
  persist_for: "4 hours"

  join: users {
    sql_on: ${orders.user_id} = ${users.id} ;;
  }
}
