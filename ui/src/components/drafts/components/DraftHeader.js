import React from "react";

import Box from "grommet/components/Box";

import { Route } from "react-router-dom";

import DraftEditorHeader from "./DraftEditorHeader";
import DraftDefaultHeader from "./DraftDefaultHeader";
import DraftActionsLayer from "./DraftActionsLayer";

import PropTypes from "prop-types";

class DraftHeader extends React.Component {
  render() {
    return (
      <Box colorIndex="grey-3-a" flex={false} justify="between" direction="row">
        <DraftDefaultHeader />
        <Box size={{ width: "medium" }}>
          <Route
            path="/drafts/:draft_id/edit"
            render={props => (
              <DraftEditorHeader {...props} formRef={this.props.formRef} />
            )}
          />
        </Box>
        <DraftActionsLayer />
      </Box>
    );
  }
}

DraftHeader.propTypes = {
  formRef: PropTypes.object
};

export default DraftHeader;
