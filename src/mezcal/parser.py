from __future__ import annotations

import hashlib
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import cast

from lxml import etree

from .errors import ParseError
from .models import Account, CEPQuery, Transfer


def _attribute(element: etree._Element, *names: str, default: str = "NA") -> str:
    for name in names:
        value = element.attrib.get(name)
        if value is not None:
            return value
    return default


def _account(element: etree._Element | None, role: str) -> Account:
    if element is None:
        return Account()
    bank_fields = (
        ("BancoEmisor", "InstitucionEmisora")
        if role == "ordenante"
        else ("BancoReceptor", "InstitucionReceptora")
    )
    return Account(
        nombre=_attribute(element, "Nombre"),
        tipo_cuenta=_attribute(element, "TipoCuenta"),
        banco=_attribute(element, *bank_fields),
        numero=_attribute(element, "Cuenta"),
        rfc=_attribute(element, "RFC"),
    )


def _parse_credit_datetime(root: etree._Element) -> datetime | None:
    for key in ("FechaAbono", "fechaAbono"):
        value = root.attrib.get(key)
        if value:
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

    cadena = root.attrib.get("cadenaCDA") or root.attrib.get("CadenaOriginal")
    if not cadena:
        return None
    pieces = cadena.split("|")
    if len(pieces) > 5:
        try:
            return datetime.strptime(pieces[4] + pieces[5], "%d%m%Y%H%M%S")
        except ValueError:
            return None
    return None


def _parse_payment_type(root: etree._Element) -> int | None:
    direct = root.attrib.get("TipoPago")
    if direct and direct.isdigit():
        return int(direct)
    cadena = root.attrib.get("cadenaCDA") or root.attrib.get("CadenaOriginal")
    if cadena:
        pieces = cadena.split("|")
        if len(pieces) > 2 and pieces[2].isdigit():
            return int(pieces[2])
    return None


def parse_cep_xml(xml: bytes, query: CEPQuery) -> Transfer:
    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False)
        root = etree.fromstring(xml, parser=parser)
    except (etree.XMLSyntaxError, ValueError) as exc:
        raise ParseError("Banxico devolvió un XML que Mezcal no pudo interpretar.") from exc

    ordenante_el = cast(etree._Element | None, root.find("Ordenante"))
    beneficiario_el = cast(etree._Element | None, root.find("Beneficiario"))
    fecha_text = root.attrib.get("FechaOperacion") or query.fecha.isoformat()
    try:
        fecha_operacion = date.fromisoformat(fecha_text)
    except ValueError as exc:
        raise ParseError("El CEP no contiene una fecha de operación válida.") from exc

    iva_text = (
        beneficiario_el.attrib.get("IVA", "0") if beneficiario_el is not None else "0"
    )
    try:
        iva = Decimal(iva_text)
    except InvalidOperation:
        iva = Decimal("0")

    concepto = (
        beneficiario_el.attrib.get("Concepto", "")
        if beneficiario_el is not None
        else ""
    )

    return Transfer(
        fecha_operacion=fecha_operacion,
        fecha_abono=_parse_credit_datetime(root),
        ordenante=_account(ordenante_el, "ordenante"),
        beneficiario=_account(beneficiario_el, "beneficiario"),
        monto=query.monto,
        iva=iva,
        concepto=concepto,
        clave_rastreo=query.clave_rastreo,
        emisor=query.emisor,
        receptor=query.receptor,
        sello=root.attrib.get("sello", ""),
        numero_certificado=(
            root.attrib.get("numeroCertificado")
            or root.attrib.get("NumeroCertificado")
        ),
        cadena_original=(
            root.attrib.get("cadenaCDA") or root.attrib.get("CadenaOriginal")
        ),
        tipo_pago=_parse_payment_type(root),
        pago_a_banco=query.pago_a_banco,
        xml_sha256=hashlib.sha256(xml).hexdigest(),
    )
