import xml.etree.ElementTree as ET

from lib.debat.models import CompteRendu, DebatParseResult, Intervention, PointSeance

AN_NS = "http://schemas.assemblee-nationale.fr/referentiel"
NS = {"an": AN_NS}


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", maxsplit=1)[1]
    return tag


def _extract_text(element: ET.Element | None) -> str:
    if element is None:
        return ""

    parts: list[str] = []
    if element.text:
        parts.append(element.text)

    for child in element:
        if _local_name(child.tag) == "br":
            parts.append("\n")
        else:
            parts.append(_extract_text(child))

        if child.tail:
            parts.append(child.tail)

    return "".join(parts).strip()


def _find_text(node: ET.Element | None, path: str) -> str | None:
    if node is None:
        return None

    value = node.findtext(path, default=None, namespaces=NS)
    if value is None:
        return None
    value = value.strip()
    return value or None


def parse_debat_file(xml_content: str) -> DebatParseResult:
    root = ET.fromstring(xml_content)

    compte_rendu_uid = _find_text(root, "an:uid")

    compte_rendu = CompteRendu(
        uid=compte_rendu_uid,
        seance_ref=_find_text(root, "an:seanceRef"),
        session_ref=_find_text(root, "an:sessionRef"),
        date_seance=_find_text(root, "an:metadonnees/an:dateSeance"),
        date_seance_jour=_find_text(root, "an:metadonnees/an:dateSeanceJour"),
        num_seance_jour=_find_text(root, "an:metadonnees/an:numSeanceJour"),
        num_seance=_find_text(root, "an:metadonnees/an:numSeance"),
        type_assemblee=_find_text(root, "an:metadonnees/an:typeAssemblee"),
        legislature=_find_text(root, "an:metadonnees/an:legislature"),
        session=_find_text(root, "an:metadonnees/an:session"),
        etat=_find_text(root, "an:metadonnees/an:etat"),
        diffusion=_find_text(root, "an:metadonnees/an:diffusion"),
        version=_find_text(root, "an:metadonnees/an:version"),
    )

    points: list[PointSeance] = []
    interventions: list[Intervention] = []

    contenu = root.find("an:contenu", NS)
    if contenu is not None:
        for section in contenu:
            section_tag = _local_name(section.tag)
            if section_tag not in {
                "point",
                "ouvertureSeance",
                "clotureSeance",
                "suspensionSeance",
                "repriseSeance",
            }:
                continue

            point_id = section.attrib.get("id_syceron")
            point_valeur = section.attrib.get("valeur_ptsodj")
            points.append(
                PointSeance(
                    compte_rendu_uid=compte_rendu_uid,
                    point_id=point_id,
                    point_type=section_tag,
                    valeur_ptsodj=point_valeur,
                    nivpoint=section.attrib.get("nivpoint"),
                    ordinal_prise=section.attrib.get("ordinal_prise"),
                    ordre_absolu_seance=section.attrib.get("ordre_absolu_seance"),
                    code_grammaire=section.attrib.get("code_grammaire"),
                    code_style=section.attrib.get("code_style"),
                    sommaire=section.attrib.get("sommaire"),
                    titre=_extract_text(section.find("an:texte", NS)),
                )
            )

            for paragraphe in section.findall("an:paragraphe", NS):
                first_orateur = paragraphe.find("an:orateurs/an:orateur", NS)
                interventions.append(
                    Intervention(
                        compte_rendu_uid=compte_rendu_uid,
                        point_id=point_id,
                        point_valeur_ptsodj=point_valeur,
                        intervention_id=paragraphe.attrib.get("id_syceron"),
                        ordre_absolu_seance=paragraphe.attrib.get(
                            "ordre_absolu_seance"
                        ),
                        ordinal_prise=paragraphe.attrib.get("ordinal_prise"),
                        code_grammaire=paragraphe.attrib.get("code_grammaire"),
                        code_style=paragraphe.attrib.get("code_style"),
                        code_parole=paragraphe.attrib.get("code_parole"),
                        roledebat=paragraphe.attrib.get("roledebat"),
                        orateur_nom=_find_text(first_orateur, "an:nom"),
                        orateur_id=_find_text(first_orateur, "an:id"),
                        orateur_qualite=_find_text(first_orateur, "an:qualite"),
                        texte=_extract_text(paragraphe.find("an:texte", NS)),
                    )
                )

    return DebatParseResult(
        comptes_rendus=[compte_rendu],
        points=points,
        interventions=interventions,
    )


def parse_debats_files(file_contents: list[str]) -> DebatParseResult:
    comptes_rendus: list[CompteRendu] = []
    points: list[PointSeance] = []
    interventions: list[Intervention] = []

    for debat_xml_content in file_contents:
        parsed = parse_debat_file(debat_xml_content)
        comptes_rendus.extend(parsed.comptes_rendus)
        points.extend(parsed.points)
        interventions.extend(parsed.interventions)

    return DebatParseResult(
        comptes_rendus=comptes_rendus,
        points=points,
        interventions=interventions,
    )
