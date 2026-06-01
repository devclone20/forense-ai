"""
Unit tests for the case state machine.

Zero I/O — these are pure domain tests, always fast.
"""
import pytest

from app.domain.case_state_machine import (
    ALLOWED_TRANSITIONS,
    JustificationRequired,
    TransitionError,
    validate_transition,
)


class TestAllowedForwardTransitions:
    def test_aberto_to_em_investigacao(self):
        result = validate_transition("aberto", "em_investigacao")
        assert result.to_status == "em_investigacao"
        assert not result.requires_justification

    def test_em_investigacao_to_em_revisao(self):
        result = validate_transition("em_investigacao", "em_revisao")
        assert result.to_status == "em_revisao"

    def test_em_revisao_to_fechado(self):
        result = validate_transition("em_revisao", "fechado")
        assert result.sets_closed_at is True

    def test_fechado_to_arquivado(self):
        result = validate_transition("fechado", "arquivado")
        assert result.sets_archived_at is True

    def test_all_forward_paths_valid(self):
        forward = [
            ("aberto", "em_investigacao"),
            ("em_investigacao", "em_revisao"),
            ("em_revisao", "fechado"),
            ("fechado", "arquivado"),
        ]
        for from_s, to_s in forward:
            result = validate_transition(from_s, to_s)
            assert result.to_status == to_s


class TestBackwardTransitionsRequireJustification:
    def test_em_investigacao_back_to_aberto_needs_justification(self):
        with pytest.raises(JustificationRequired):
            validate_transition("em_investigacao", "aberto")

    def test_em_investigacao_back_to_aberto_with_justification(self):
        result = validate_transition(
            "em_investigacao", "aberto", justification="Error in classification"
        )
        assert result.requires_justification is True
        assert result.from_status == "em_investigacao"

    def test_em_revisao_back_to_em_investigacao_needs_justification(self):
        with pytest.raises(JustificationRequired):
            validate_transition("em_revisao", "em_investigacao")

    def test_fechado_back_to_em_investigacao_needs_justification(self):
        with pytest.raises(JustificationRequired):
            validate_transition("fechado", "em_investigacao")


class TestInvalidTransitions:
    def test_cannot_skip_from_aberto_to_fechado(self):
        with pytest.raises(TransitionError):
            validate_transition("aberto", "fechado")

    def test_cannot_skip_from_aberto_to_arquivado(self):
        with pytest.raises(TransitionError):
            validate_transition("aberto", "arquivado")

    def test_cannot_go_backwards_from_arquivado_without_admin(self):
        with pytest.raises(TransitionError):
            validate_transition("arquivado", "fechado", is_admin=False)

    def test_admin_can_reopen_from_arquivado(self):
        result = validate_transition("arquivado", "fechado", is_admin=True)
        assert result.to_status == "fechado"

    def test_cannot_transition_to_same_state(self):
        with pytest.raises(TransitionError):
            validate_transition("aberto", "aberto")

    def test_invalid_target_state_raises(self):
        with pytest.raises(TransitionError):
            validate_transition("aberto", "nonexistent_state")


class TestSideEffects:
    def test_closing_a_case_sets_closed_at(self):
        result = validate_transition("em_revisao", "fechado")
        assert result.sets_closed_at is True
        assert result.sets_archived_at is False

    def test_archiving_sets_archived_at(self):
        result = validate_transition("fechado", "arquivado")
        assert result.sets_archived_at is True
        assert result.sets_closed_at is False

    def test_reopening_from_fechado_clears_closed_at(self):
        result = validate_transition(
            "fechado", "em_investigacao", justification="Needs reinvestigation"
        )
        assert result.clears_closed_at is True

    def test_forward_transition_does_not_clear_closed_at(self):
        result = validate_transition("aberto", "em_investigacao")
        assert result.clears_closed_at is False


class TestTransitionGraph:
    def test_arquivado_has_no_allowed_transitions(self):
        assert ALLOWED_TRANSITIONS["arquivado"] == []

    def test_all_statuses_present_in_graph(self):
        expected = {"aberto", "em_investigacao", "em_revisao", "fechado", "arquivado"}
        assert set(ALLOWED_TRANSITIONS.keys()) == expected
