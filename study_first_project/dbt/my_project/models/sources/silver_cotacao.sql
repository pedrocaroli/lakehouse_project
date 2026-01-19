{{ config(materialized='table', unique_key='id') }}

with df as (
    select *
    from {{ ref('bronze_cotacao_data') }}
    where create_date is not null
),

ranked as (
    select
        concat(code, '_', timestamp) as id,
        *,
        row_number() over (
            partition by code, timestamp
            order by create_date desc
        ) as rn
    from df
)

select *
from ranked
where rn = 1
