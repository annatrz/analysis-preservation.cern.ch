import React from "react";
import PropTypes from "prop-types";

import { connect } from "react-redux";

import Anchor from "grommet/components/Anchor";
import Box from "grommet/components/Box";

import Edit from "grommet/components/icons/base/FormEdit";
import { toggleFilemanagerLayer } from "../../../../../../actions/drafts";

class ImportDataField extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <Box
        pad={{ horizontal: "medium" }}
        size={{ width: "xxlarge" }}
        justify="center"
        flex={false}
        alignSelf="end"
        wrap={true}
        style={{ overflow: "hidden" }}
      >
        {this.props.formData || ""}
      </Box>
    );
  }
}

ImportDataField.propTypes = {
  formData: PropTypes.object
};

export default ImportDataField;
