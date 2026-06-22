from lib.debat.parsing import parse_debat_file, parse_debats_files


def test_parse_debat_file_extracts_compte_rendu_points_interventions() -> None:
    xml_content = _build_xml(
        uid="CRSANR5L17S2025O1N001",
        point_id="3511370",
        intervention_id="3511371",
    )

    parsed = parse_debat_file(xml_content)

    assert len(parsed.comptes_rendus) == 1
    assert len(parsed.points) == 1
    assert len(parsed.interventions) == 1

    compte_rendu = parsed.comptes_rendus[0]
    assert compte_rendu.uid == "CRSANR5L17S2025O1N001"
    assert compte_rendu.seance_ref == "SEANCE-CRSANR5L17S2025O1N001"
    assert compte_rendu.session_ref == "SESSION-CRSANR5L17S2025O1N001"
    assert compte_rendu.type_assemblee == "AN"
    assert compte_rendu.legislature == "17"

    point = parsed.points[0]
    assert point.compte_rendu_uid == "CRSANR5L17S2025O1N001"
    assert point.point_id == "3511370"
    assert point.point_type == "point"
    assert point.titre == "Déclaration du Gouvernement"

    intervention = parsed.interventions[0]
    assert intervention.compte_rendu_uid == "CRSANR5L17S2025O1N001"
    assert intervention.point_id == "3511370"
    assert intervention.intervention_id == "3511371"
    assert intervention.orateur_nom == "Mme la présidente"
    assert intervention.orateur_id == "721908"
    assert intervention.orateur_qualite == "Présidente"
    assert intervention.texte == "Bonjour\nle monde (applaudissements)"


def test_parse_debats_files_aggregates_multiple_xml_documents() -> None:
    xml_1 = _build_xml(
        uid="CRSANR5L17S2025O1N001",
        point_id="3511370",
        intervention_id="3511371",
    )
    xml_2 = _build_xml(
        uid="CRSANR5L17S2025O1N002",
        point_id="3512370",
        intervention_id="3512371",
    )

    parsed = parse_debats_files([xml_1, xml_2])

    assert len(parsed.comptes_rendus) == 2
    assert len(parsed.points) == 2
    assert len(parsed.interventions) == 2

    assert parsed.comptes_rendus[0].uid == "CRSANR5L17S2025O1N001"
    assert parsed.comptes_rendus[1].uid == "CRSANR5L17S2025O1N002"
    assert parsed.points[0].compte_rendu_uid == "CRSANR5L17S2025O1N001"
    assert parsed.points[1].compte_rendu_uid == "CRSANR5L17S2025O1N002"
    assert parsed.points[0].point_id == "3511370"
    assert parsed.points[1].point_id == "3512370"
    assert parsed.interventions[0].intervention_id == "3511371"
    assert parsed.interventions[1].intervention_id == "3512371"


def _build_xml(uid: str, point_id: str, intervention_id: str) -> str:
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<compteRendu xmlns=\"http://schemas.assemblee-nationale.fr/referentiel\">
  <uid>{uid}</uid>
  <seanceRef>SEANCE-{uid}</seanceRef>
  <sessionRef>SESSION-{uid}</sessionRef>
  <metadonnees>
    <dateSeance>20241001150000000</dateSeance>
    <dateSeanceJour>mardi 01 octobre 2024</dateSeanceJour>
    <numSeanceJour>Unique</numSeanceJour>
    <numSeance>1</numSeance>
    <typeAssemblee>AN</typeAssemblee>
    <legislature>17</legislature>
    <session>Session ordinaire 2024-2025</session>
    <etat>complet</etat>
    <diffusion>public</diffusion>
    <version>avant_JO</version>
  </metadonnees>
  <contenu>
    <quantiemes>
      <journee>Séance test</journee>
    </quantiemes>
    <point
      id_syceron=\"{point_id}\"
      valeur_ptsodj=\"4\"
      nivpoint=\"1\"
      ordinal_prise=\"1\"
      ordre_absolu_seance=\"16\"
      code_grammaire=\"TITRE\"
      code_style=\"Titre\"
      sommaire=\"1\"
    >
      <texte>Déclaration du Gouvernement</texte>
      <paragraphe
        id_syceron=\"{intervention_id}\"
        ordre_absolu_seance=\"17\"
        ordinal_prise=\"1\"
        code_grammaire=\"PAROLE_GENERIQUE\"
        code_style=\"NORMAL\"
        code_parole=\"\"
        roledebat=\"president\"
      >
        <orateurs>
          <orateur>
            <nom>Mme la présidente</nom>
            <id>721908</id>
            <qualite>Présidente</qualite>
          </orateur>
        </orateurs>
        <texte>Bonjour<br/>le monde <italique>(applaudissements)</italique></texte>
      </paragraphe>
    </point>
  </contenu>
</compteRendu>
"""
