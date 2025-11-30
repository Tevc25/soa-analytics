# soa-analytics

Storitev za analitiko (mesečni “budget vs spent” in poraba zadnjih 7 dni), ki bere podatke iz `soa-category-budget` in rezultate shranjuje v lastno MongoDB bazo (`analytics_db`).

## Namestitev in zagon

### Docker
```bash
# v mapi soa-expenseTracker
docker compose build soa-analytics
docker compose up -d soa-analytics
# lokalni port: 8003 -> container port: 8003
```

### Okoljske spremenljivke (`.env`)
- `MONGO_URI` – povezava na MongoDB Atlas.
- `MONGO_DB` – ime baze (npr. `analytics_db`).
- `CATEGORY_BUDGET_URL` – URL do category-budget servisa; v docker mreži naj bo `http://soa-category-budget:8002`, lokalno pa `http://localhost:8002`.
- `CORS_ORIGINS` – (opcijsko) seznam originov ločenih z vejico (npr. `http://localhost:5173,http://localhost:3000`).
- `PORT` – (opcijsko) port za zagon (privzeto `8003`).

## Struktura podatkov

### Monthly analytics (Mongo dokument, kolekcija `monthly_data`)
```json
{
  "_id": "<ObjectId>",
  "user_id": "<user-id>",
  "month": "2025-11",
  "rows": [
    {
      "category_id": "<category ObjectId>",
      "category_name": "Nakup hrane",
      "budget": 366.0,
      "spent": 45.5
    }
  ],
  "created_at": "2025-11-30T15:53:16.137000",
  "updated_at": "2025-11-30T15:53:16.137000"
}
```

### Weekly analytics (Mongo dokument, kolekcija `weekly_data`)
Weekly je narejen kot “last7days” (zadnjih 7 dni od danes).
```json
{
  "_id": "<ObjectId>",
  "user_id": "<user-id>",
  "type": "last7days",
  "days": [
    { "date": "2025-11-24", "spent": 10.0 },
    { "date": "2025-11-25", "spent": 0.0 }
  ],
  "created_at": "2025-11-30T15:53:16.137000",
  "updated_at": "2025-11-30T15:53:16.137000"
}
```

## API (base: `http://localhost:8003`)

### Monthly (budget vs spent)
- **POST** `/{user_id}/analytics/monthly/generate`  
  Body: `{ "month": "YYYY-MM" }`  
  Izračuna analitiko za mesec: budgete prebere iz `/{user_id}/budgets?month=...`, porabo pa iz kategorij in njihovih itemov (`/{user_id}/categories`). Rezultat shrani v `monthly_data`.

- **GET** `/{user_id}/analytics/monthly?month=YYYY-MM`  
  Vrne shranjeno analitiko za izbran mesec.

- **PUT** `/{user_id}/analytics/monthly/{month}/recompute`  
  Ponovno izračuna in posodobi shranjene podatke za mesec.

- **DELETE** `/{user_id}/analytics/monthly/{month}/delete`  
  Izbriše shranjeno analitiko za mesec.

### Weekly (last 7 days)
- **POST** `/{user_id}/analytics/weekly/last7/generate`  
  Brez body-ja. Izračuna porabo za zadnjih 7 dni in shrani v `weekly_data` (`type = "last7days"`).

- **GET** `/{user_id}/analytics/weekly/last7`  
  Vrne shranjeno analitiko “zadnjih 7 dni”.

- **PUT** `/{user_id}/analytics/weekly/last7/recompute`  
  Brez body-ja. Ponovno izračuna in posodobi “zadnjih 7 dni”.

- **DELETE** `/{user_id}/analytics/weekly/last7/delete`  
  Izbriše shranjeno analitiko “zadnjih 7 dni”.

## Opombe
- Storitev se povezuje na `soa-category-budget` prek `CATEGORY_BUDGET_URL` in uporablja endpointa:
  - `GET /{user_id}/categories` (kategorije + itemi)
  - `GET /{user_id}/budgets?month=YYYY-MM` (budgeti za mesec)
- Za pravilne mesečne/tedenske izračune morajo itemi vsebovati `created_at` (ISO string), da se lahko filtrira po datumu.
- Datumi `created_at` in `updated_at` se vračajo formatirano (glej Pydantic serializerje).