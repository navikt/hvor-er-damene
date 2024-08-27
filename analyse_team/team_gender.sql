with siste_mnd as (select *
                   from teamkatalogen.monthly_snapshot_raw
                   where lastet_dato = (select max(lastet_dato) from teamkatalogen.monthly_snapshot_raw)),
    fortsatt_ansatt as (select *
                        from siste_mnd
                        where (Sluttdato is null)),
    data as (select fa.*, gp.gender_pred
             from fortsatt_ansatt fa
             left join (select Ident, gender_pred
                        from teamkatalogen.teamkat_gender_pred
                        where dato_mnd = (select max(dato_mnd) from teamkatalogen.teamkat_gender_pred)) as gp
                       on gp.Ident = fa.Ident)
select Team, gender_pred, Roller
from data
order by Team
