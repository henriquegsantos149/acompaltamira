"""Contratos de acompanhamento. Valores ausentes permanecem None."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Registro(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, str_strip_whitespace=True)
    responsavel_informacao: str = Field(min_length=1)
    evidencia_arquivo_ou_url: str = Field(min_length=1)
    pagina_evidencia: int | None = Field(default=None, ge=1)
    observacao: str | None = None
    data_registro: datetime | None = None
    revisao_esperada: int | None = Field(default=None, ge=1)
    justificativa_retificacao: str | None = None

    @field_validator('data_registro')
    @classmethod
    def timezone(cls, v):
        if v is not None and v.utcoffset() is None:
            raise ValueError('Data de registro exige fuso horário.')
        return v

    @field_validator('*', mode='before')
    @classmethod
    def reject_boolean_numbers(cls, v, info):
        if v is not None and info.field_name in {'numerador','denominador','valor_medido','quantidade_executada','valor_empenhado','valor_liquidado','valor_pago','revisao_esperada','pagina_evidencia'} and (isinstance(v,bool) or not isinstance(v,(int,float))):
            raise ValueError('Informe número JSON, sem texto ou booleano; ausência deve ser null.')
        return v

    @model_validator(mode='after')
    def periods(self):
        for start,end in [('periodo_inicio','periodo_fim'),('inicio_real','conclusao_real')]:
            a,b=getattr(self,start,None),getattr(self,end,None)
            if a and b and a>b:
                raise ValueError('Início posterior ao fim do período.')
        return self


class Medicao(Registro):
    medicao_id: str = Field(min_length=1, max_length=150)
    indicador_id: str = Field(min_length=1)
    ambito: str = Field(min_length=1)
    periodo_inicio: date
    periodo_fim: date
    numerador: float | None = Field(default=None, ge=0)
    denominador: float | None = Field(default=None, gt=0)
    valor_medido: float | None = None
    unidade: str = Field(min_length=1)


class Execucao(Registro):
    execucao_id: str = Field(min_length=1, max_length=150)
    acao_id: str = Field(min_length=1)
    projeto_id: str | None = None
    localidade: str = Field(min_length=1)
    data_referencia: date
    situacao_informada: str = Field(min_length=1)
    quantidade_executada: float | None = Field(default=None, ge=0)
    unidade: str = Field(min_length=1)
    inicio_real: date | None = None
    conclusao_real: date | None = None


class Financeiro(Registro):
    despesa_id: str = Field(min_length=1, max_length=150)
    linha_investimento_id: str = Field(min_length=1)
    acao_id: str | None = None
    localidade: str = Field(min_length=1)
    periodo_inicio: date
    periodo_fim: date
    valor_empenhado: float | None = Field(default=None, ge=0)
    valor_liquidado: float | None = Field(default=None, ge=0)
    valor_pago: float | None = Field(default=None, ge=0)
    unidade_monetaria: Literal['R$']
    data_base: date | None = None


class Decisao(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    decisao_id: str = Field(min_length=1, max_length=150)
    indicador_id: str = Field(min_length=1)
    meta_id: str = Field(min_length=1)
    ambito: str = Field(min_length=1)
    responsavel: str = Field(min_length=1)
    justificativa: str = Field(min_length=1)
    data_registro: datetime

    @field_validator('data_registro')
    @classmethod
    def timezone(cls,v):
        if v.utcoffset() is None:
            raise ValueError('Informe fuso horário.')
        return v


MODELS={'medicoes': Medicao,'execucoes':Execucao,'financeiro':Financeiro}
IDS={'medicoes':'medicao_id','execucoes':'execucao_id','financeiro':'despesa_id','decisoes':'decisao_id'}
